"""
Quiz Agent for Stud
Generates medical quiz questions from AI knowledge, documents, or internet
Supports multiple choice, true/false, and open-ended questions
"""
import os
from typing import Optional, List, Dict, Any, Union, Literal, Tuple
from pydantic_ai import Agent
from pydantic import BaseModel
import asyncio
import json
import uuid
import random
from datetime import datetime

from configs.config import config
from model import select_model
from agents.agents import get_quiz_model
from models.states import Quiz, QuizQuestion, OpenEndedAnswer, DifficultyLevel
from utils import search_internet
from service.document_processor import get_document_processor
from service.database import get_database_service


class QuizAgent:
    """
    Quiz Agent for creating medical quiz questions
    Supports both multiple choice and open-ended questions with optional internet access
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None, 
        api_key: Optional[str] = None, 
        provider: str = "google",
        use_internet: bool = True
    ):
        """
        Initialize the Quiz Agent
        
        Args:
            model_name: Model name
            api_key: API key
            provider: "google" or "openai"
            use_internet: Whether to enable internet search
        """

        self.use_internet = use_internet
        self._model_name = model_name
        self._api_key = api_key

        model = get_quiz_model(self._model_name, self._api_key)
        
        self.system_prompt = """
        You are a medical education expert creating quiz questions.
        Generate high-quality, medically accurate questions that test understanding of medical concepts.
        
        For multiple choice questions, provide options (should be relevant to the question) with only one correct answer.
        For true/false questions, provide exactly 2 options (True/False) with only one correct answer.
        For open-ended questions, ask questions that require detailed explanations (theory).
        
        Always provide clear explanations for the correct answers.
        Focus on practical knowledge that would be useful for user based on their field or profession.
        """
        
        if use_internet:
            self.system_prompt += """
        
        You have access to internet search for current information. Use it when:
        - Questions require recent medical guidelines or protocols
        - Current treatment recommendations are needed
        - Latest research findings are relevant
        - generating very domain specific questions
        """
        
        # Register internet search tool if enabled
        tools = []
        if use_internet:
            @Agent.tool
            async def search_web(query: str) -> str:
                """Search the internet for current medical information"""
                return await search_internet(query, api_key)
            tools.append(search_web)
        
        self.agent = Agent(
            model,
            system_prompt=self.system_prompt,
            output_type=List[QuizQuestion],
            tools=tools if tools else None
        )

        # Refine sub-agent for question quality improvement
        refine_model = get_quiz_model(self._model_name, self._api_key)
        self._refine_agent = Agent(
            refine_model,
            system_prompt="You are a medical education expert. Refine quiz questions for clarity, accuracy, and educational value. Preserve question structure (type, options, correct_answer). Return refined questions in the same order.",
            output_type=List[QuizQuestion]
        )
        
        # Initialize scoring agent (reused for efficiency)
        self.scoring_agent = None
        
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model with new user-provided credentials."""
        if model_name is not None:
            self._model_name = model_name
        if api_key is not None:
            self._api_key = api_key

        resolved_model = self._model_name or getattr(config, 'QUIZ_MODEL_NAME', None) or "gemini-2.0-flash"
        model = get_quiz_model(resolved_model, self._api_key)

        tools = []
        if self.use_internet:
            search_key = self._api_key or config.OPENROUTER_API_KEY or ""

            @Agent.tool
            async def search_web(query: str) -> str:
                """Search the internet for current medical information"""
                return await search_internet(query, search_key)
            tools.append(search_web)

        self.agent = Agent(
            model,
            system_prompt=self.system_prompt,
            output_type=List[QuizQuestion],
            tools=tools if tools else None
        )
        self.scoring_agent = None
    
    async def generate_quiz(
        self,
        text_content: Optional[str] = None,
        from_document: bool = False,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        from_internet: bool = False,
        num_questions: int = 40,
        quiz_type: str = "general",
        user_subject_of_study: Optional[str] = None,
        user_profession: Optional[str] = None,
        time_limit: int = 600,
        num_multiple_choice: Optional[int] = None,
        num_true_false: Optional[int] = None,
        num_open_ended: Optional[int] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        context: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: str = "google"
    ) -> Quiz:
        """
        Generate a medical quiz using AI.
        
        Logic:
        1. Determine source (document, knowledge, or internet)
        2. Generate questions based on source
        3. Rerank questions for quality
        4. Refine top N questions
        5. Return Quiz object
        
        Args:
            text_content: Raw text content (if provided)
            from_document: Whether to generate from document
            file_path: Path to file (if provided)
            document_id: Document ID in database (if provided)
            from_internet: Whether to use internet search
            num_questions: Total number of questions
            quiz_type: Type of quiz ("general", "specialized", etc.)
            user_subject_of_study: Subject/field of study
            time_limit: Time limit in seconds
            num_multiple_choice: Number of multiple choice questions
            num_true_false: Number of true/false questions
            num_open_ended: Number of open-ended questions
            difficulty_level: Difficulty level
            context: Additional context
            model_name: Optional model name override
            api_key: Optional API key override
            provider: Model provider
            
        Returns:
            Quiz object with generated questions
        """
        # Reinitialize model if parameters changed
        if model_name or api_key:
            self._reinitialize_model(model_name, api_key)
        
        # Determine question distribution (randomized when all unspecified)
        if num_multiple_choice is None and num_open_ended is None and num_true_false is None:
            mc_pct = random.uniform(0.5, 0.85)
            tf_pct = random.uniform(0.1, 0.35)
            mc_pct = min(mc_pct, 1 - tf_pct - 0.05)
            num_multiple_choice = max(1, int(num_questions * mc_pct))
            num_true_false = max(0, int(num_questions * tf_pct))
            num_open_ended = num_questions - num_multiple_choice - num_true_false
        elif num_multiple_choice is None:
            num_multiple_choice = num_questions - (num_open_ended or 0) - (num_true_false or 0)
        elif num_open_ended is None:
            num_open_ended = num_questions - (num_multiple_choice or 0) - (num_true_false or 0)
        elif num_true_false is None:
            num_true_false = num_questions - (num_multiple_choice or 0) - (num_open_ended or 0)
        
        # Generate questions based on source
        if from_document and (document_id or file_path or text_content):
            quiz = await self.generate_questions_from_document(
                text_content=text_content,
                from_vector_db=True,
                document_id=document_id,
                file_path=file_path,
                user_id=user_id,
                quiz_type=quiz_type,
                num_questions=num_questions,
                time_limit=time_limit,
                context=context,
                num_multiple_choice=num_multiple_choice,
                num_true_false=num_true_false,
                num_open_ended=num_open_ended,
                difficulty_level=difficulty_level,
                user_subject_of_study=user_subject_of_study or user_profession
            )
        else:
            subject_or_profession = user_subject_of_study or user_profession or "general medicine"
            quiz = await self.generate_questions_from_knowledge(
                quiz_type=quiz_type,
                user_subject_of_study=subject_or_profession,
                num_questions=num_questions,
                time_limit=time_limit,
                context=context,
                num_multiple_choice=num_multiple_choice,
                num_true_false=num_true_false,
                num_open_ended=num_open_ended,
                difficulty_level=difficulty_level,
                user_profession=user_profession,
            )
        
        # Set source
        quiz.source = "document" if from_document else "AI_knowledge"
        
        return quiz
    
    async def generate_questions_from_knowledge(
        self,
        quiz_type,
        user_subject_of_study: str,
        num_questions: int = 40,
        time_limit: int = 600,
        context: Optional[str] = None,
        num_multiple_choice: Optional[int] = None,
        num_true_false: Optional[int] = None,
        num_open_ended: Optional[int] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        n_subtopics: int = 10,
        user_profession: Optional[str] = None,
    ) -> Quiz:
        """
        Generate quiz questions from AI knowledge base.
        
        Process:
        1. Generate subtopics under user's subject of study/profession
        2. Randomly select subtopics
        3. Generate n questions for each subtopic in parallel
        4. Combine and return Quiz

        Returns:
            Quiz object
        """
        # Determine question distribution (randomized when all unspecified)
        if num_multiple_choice is None and num_open_ended is None and num_true_false is None:
            mc_pct = random.uniform(0.5, 0.85)
            tf_pct = random.uniform(0.1, 0.35)
            mc_pct = min(mc_pct, 1 - tf_pct - 0.05)
            num_multiple_choice = max(1, int(num_questions * mc_pct))
            num_true_false = max(0, int(num_questions * tf_pct))
            num_open_ended = num_questions - num_multiple_choice - num_true_false
        elif num_multiple_choice is None:
            num_multiple_choice = num_questions - (num_open_ended or 0) - (num_true_false or 0)
        elif num_open_ended is None:
            num_open_ended = num_questions - (num_multiple_choice or 0) - (num_true_false or 0)
        elif num_true_false is None:
            num_true_false = num_questions - (num_multiple_choice or 0) - (num_open_ended or 0)

        # Generate subtopics
        subtopics = await self._generate_subtopics(
            subject=user_subject_of_study,
            profession=user_profession,
            n_subtopics=n_subtopics,
        )
        
        # Select random subtopics (enough to generate num_questions)
        questions_per_subtopic = max(1, num_questions // len(subtopics))
        selected_subtopics = random.sample(subtopics, min(len(subtopics), (num_questions + questions_per_subtopic - 1) // questions_per_subtopic))
        
        # Generate questions for each subtopic in parallel
        tasks = []
        for subtopic in selected_subtopics:
            # Distribute question types across subtopics
            mc_per_subtopic = max(1, num_multiple_choice // len(selected_subtopics))
            tf_per_subtopic = max(0, num_true_false // len(selected_subtopics)) if num_true_false else 0
            oe_per_subtopic = max(0, num_open_ended // len(selected_subtopics)) if num_open_ended else 0
            
            task = self._generate_questions_for_subtopic(
                subtopic=subtopic,
                num_multiple_choice=mc_per_subtopic,
                num_true_false=tf_per_subtopic,
                num_open_ended=oe_per_subtopic,
                difficulty_level=difficulty_level,
                time_limit=time_limit,
                context=context
            )
            tasks.append(task)
        
        # Execute in parallel
        question_lists = await asyncio.gather(*tasks)
        
        # Flatten and combine questions
        all_questions = []
        for q_list in question_lists:
            all_questions.extend(q_list)
        
        # Rerank questions for quality
        ranked_questions = await self.rerank_questions(all_questions)
        
        # Take top N questions
        final_questions = ranked_questions[:num_questions]
        
        # Refine questions
        refined_questions = await self.refine_reranked_questions(final_questions)
        
        # Create Quiz object
        quiz = Quiz(
            id=f"quiz_{uuid.uuid4()}",
            title=f"{user_subject_of_study} Quiz",
            questions=refined_questions,
            timeLimit=time_limit,
            totalQuestions=len(refined_questions),
            source="AI_knowledge"
        )
        
        return quiz
    
    async def _generate_subtopics(
        self, subject: Optional[str] = None, profession: Optional[str] = None, n_subtopics: int = 20
    ) -> List[str]:
        """Generate subtopics for a subject or profession using a lightweight str-list agent."""
        key = (subject or profession or "").lower()
        prompt = f"""
        Generate {n_subtopics} diverse subtopics under "{key or 'general medicine'}" for medical education.
        Return only a JSON array of subtopic names, no explanations.
        Example: ["Anatomy", "Physiology", "Pathology", ...]
        """
        try:
            if not hasattr(self, '_subtopic_agent'):
                model, _ = select_model(
                    getattr(config, 'QUIZ_MODEL_NAME', None) or "gemini-2.0-flash",
                    getattr(config, 'API_KEY', None) or "",
                )
                self._subtopic_agent = Agent(model, output_type=List[str])
            result = await self._subtopic_agent.run(prompt)
            out = result.output if hasattr(result, 'output') else result
            if isinstance(out, list) and out:
                return out[:n_subtopics]
            return self._get_default_subtopics(key, n_subtopics)
        except Exception:
            return self._get_default_subtopics(key, n_subtopics)
    
    def _get_default_subtopics(self, subject: str, n: int = 20) -> List[str]:
        """Get default subtopics from exhaustive config. Falls back to safe default if not found."""
        from configs.quiz_subtopics import DEFAULT_SUBTOPICS, SAFE_DEFAULT

        key = (subject or "").lower()
        for config_key, topics in DEFAULT_SUBTOPICS.items():
            if config_key in key or key in config_key:
                return topics[:n]
        return DEFAULT_SUBTOPICS.get(SAFE_DEFAULT, ["General Medicine"])[:n]
    
    async def _generate_questions_for_subtopic(
        self,
        subtopic: str,
        num_multiple_choice: int,
        num_true_false: int,
        num_open_ended: int,
        difficulty_level: Optional[DifficultyLevel],
        time_limit: int,
        context: Optional[str]
    ) -> List[QuizQuestion]:
        """Generate questions for a specific subtopic"""
        prompt = self.generate_prompt(
            quiz_type="general",
            num_questions=num_multiple_choice + num_true_false + num_open_ended,
            num_multiple_choice=num_multiple_choice,
            num_true_false=num_true_false,
            num_open_ended=num_open_ended,
            time_limit=time_limit,
            difficulty_level=difficulty_level,
            user_subject_of_study=subtopic,
            context=context
        )
        
        try:
            result = await self.agent.run(prompt)
            out = result.output if hasattr(result, 'output') else result
            if isinstance(out, list):
                return [q if isinstance(q, QuizQuestion) else QuizQuestion(**q) for q in out]
            return []
        except Exception as e:
            print(f"Error generating questions for subtopic {subtopic}: {e}")
            return []
    
    async def generate_questions_from_document(
        self,
        text_content: Optional[str] = None,
        from_vector_db: bool = False,
        document_id: Optional[str] = None,
        file_path: Optional[str] = None,
        user_id: Optional[str] = None,
        quiz_type: str = "general",
        num_questions: int = 40,
        time_limit: int = 600,
        context: Optional[str] = None,
        num_multiple_choice: Optional[int] = None,
        num_true_false: Optional[int] = None,
        num_open_ended: Optional[int] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        user_subject_of_study: Optional[str] = None
    ) -> Quiz:
        """
        Generate quiz questions from document content.
        
        Process:
        1. Parse and chunk document
        2. Determine questions per chunk
        3. Generate questions for each chunk in parallel
        4. Rerank and refine questions
        5. Return Quiz
        
        Args:
            text_content: Raw text content
            from_vector_db: Whether to retrieve from vector DB
            document_id: Document ID
            file_path: Path to file
            quiz_type: Type of quiz
            num_questions: Total number of questions
            time_limit: Time limit per question
            context: Additional context
            num_multiple_choice: Number of multiple choice questions
            num_true_false: Number of true/false questions
            num_open_ended: Number of open-ended questions
            difficulty_level: Difficulty level
            user_subject_of_study: Subject/field of study
            
        Returns:
            Quiz object
        """
        # Parse document and get chunks
        chunks = await self._parse_document(
            text_content=text_content,
            from_vector_db=from_vector_db,
            file_path=file_path,
            document_id=document_id,
            user_id=user_id
        )
        
        if not chunks:
            raise ValueError("No document content found")
        
        # Determine question distribution (randomized when all unspecified)
        if num_multiple_choice is None and num_open_ended is None and num_true_false is None:
            mc_pct = random.uniform(0.5, 0.85)
            tf_pct = random.uniform(0.1, 0.35)
            mc_pct = min(mc_pct, 1 - tf_pct - 0.05)
            num_multiple_choice = max(1, int(num_questions * mc_pct))
            num_true_false = max(0, int(num_questions * tf_pct))
            num_open_ended = num_questions - num_multiple_choice - num_true_false
        elif num_multiple_choice is None:
            num_multiple_choice = num_questions - (num_open_ended or 0) - (num_true_false or 0)
        elif num_open_ended is None:
            num_open_ended = num_questions - (num_multiple_choice or 0) - (num_true_false or 0)
        elif num_true_false is None:
            num_true_false = num_questions - (num_multiple_choice or 0) - (num_open_ended or 0)

        # Determine questions per chunk
        questions_per_chunk = self.determine_num_questions_per_chunk(
            n_chunks=len(chunks),
            average_words_per_chunk=sum(len(chunk.get("content", "").split()) for chunk in chunks) // len(chunks) if chunks else 1000,
            num_questions=num_questions,
            num_multiple_choice=num_multiple_choice,
            num_true_false=num_true_false,
            num_open_ended=num_open_ended
        )
        
        # Generate questions for each chunk in parallel
        tasks = []
        for i, chunk in enumerate(chunks):
            chunk_content = chunk.get("content", "")
            chunk_num_questions = questions_per_chunk[i] if i < len(questions_per_chunk) else questions_per_chunk[-1]
            
            # Distribute question types proportionally
            mc_per_chunk = max(1, int(chunk_num_questions * (num_multiple_choice / num_questions))) if num_multiple_choice else 0
            tf_per_chunk = max(0, int(chunk_num_questions * (num_true_false / num_questions))) if num_true_false else 0
            oe_per_chunk = chunk_num_questions - mc_per_chunk - tf_per_chunk
            
            task = self._generate_questions_for_chunk(
                chunk_content=chunk_content,
                chunk_index=chunk.get("chunk_index", i),
                num_multiple_choice=mc_per_chunk,
                num_true_false=tf_per_chunk,
                num_open_ended=oe_per_chunk,
                difficulty_level=difficulty_level,
                time_limit=time_limit,
                context=context
            )
            tasks.append(task)
        
        # Execute in parallel
        question_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and combine questions (handle exceptions)
        all_questions = []
        for q_list in question_lists:
            if isinstance(q_list, Exception):
                print(f"Error generating questions for chunk: {q_list}")
                continue
            all_questions.extend(q_list)
        
        # Rerank questions
        ranked_questions = await self.rerank_questions(all_questions)
        
        # Take top N questions
        final_questions = ranked_questions[:num_questions]
        
        # Refine questions with their original chunks (chunk_index -> content)
        chunk_by_index = {c.get("chunk_index", i): c.get("content", "") for i, c in enumerate(chunks)}
        refined_questions = await self.refine_reranked_questions(final_questions, chunk_by_index)
        
        # Create Quiz object
        quiz = Quiz(
            id=f"quiz_{uuid.uuid4()}",
            title=f"Document Quiz" + (f" - {user_subject_of_study}" if user_subject_of_study else ""),
            questions=refined_questions,
            timeLimit=time_limit,
            totalQuestions=len(refined_questions),
            source="document"
        )
        
        return quiz
    
    async def _generate_questions_for_chunk(
        self,
        chunk_content: str,
        chunk_index: int,
        num_multiple_choice: int,
        num_true_false: int,
        num_open_ended: int,
        difficulty_level: Optional[DifficultyLevel],
        time_limit: int,
        context: Optional[str]
    ) -> List[QuizQuestion]:
        """Generate questions for a specific chunk"""
        prompt = f"""
        {context or ""}
        
        Generate questions from this document chunk:
        
        {chunk_content[:2000]}  # Limit chunk size for prompt
        
        Generate:
        - {num_multiple_choice} multiple choice questions
        - {num_true_false} true/false questions
        - {num_open_ended} open-ended questions
        
        Difficulty: {difficulty_level or "Medium"}
        Time limit: {time_limit} seconds per question
        
        Attach chunk_index: {chunk_index} to each question for reference.
        """
        
        try:
            result = await self.agent.run(prompt)
            out = result.output if hasattr(result, 'output') else result
            if isinstance(out, list):
                questions = [q if isinstance(q, QuizQuestion) else QuizQuestion(**q) for q in out]
            else:
                questions = []

            for q in questions:
                if not hasattr(q, 'chunk_index'):
                    q.chunk_index = chunk_index

            return questions
        except Exception as e:
            print(f"Error generating questions for chunk {chunk_index}: {e}")
            return []
    
    def determine_num_questions_per_chunk(
        self,
        n_chunks: int,
        average_words_per_chunk: int,
        num_questions: int,
        num_multiple_choice: int,
        num_true_false: int,
        num_open_ended: int
    ) -> List[int]:
        """
        Determine number of questions per chunk based on chunk size.
        
        Logic:
        - Larger chunks get more questions
        - Account for filtering/reranking (generate 1.5x more than needed)
        - Distribute proportionally based on word count
        
        Args:
            n_chunks: Number of chunks
            average_words_per_chunk: Average words per chunk
            num_questions: Total questions needed
            num_multiple_choice: Number of multiple choice questions
            num_true_false: Number of true/false questions
            num_open_ended: Number of open-ended questions
            
        Returns:
            List of questions per chunk
        """
        if n_chunks == 0:
            return []
        
        # Generate 1.5x more questions than needed (for filtering)
        total_to_generate = int(num_questions * 1.5)
        
        # Base questions per chunk
        base_per_chunk = total_to_generate // n_chunks
        
        # Distribute remaining questions to larger chunks
        questions_per_chunk = [base_per_chunk] * n_chunks
        remaining = total_to_generate - (base_per_chunk * n_chunks)
        
        # Add remaining questions (distribute evenly)
        for i in range(remaining):
            questions_per_chunk[i % n_chunks] += 1
        
        return questions_per_chunk
    
    async def rerank_questions(
        self,
        questions: List[QuizQuestion],
        score_threshold: float = 0.5,
        quality_threshold: float = 0.5,
        alpha : float = 0.8,
        beta: float = 0.2
    ) -> List[QuizQuestion]:
        """
        Rerank questions based on score and quality.
        
        Process:
        1. Score each question for importance/quality
        2. Filter by thresholds
        3. Sort by score (descending)
        
        Args:
            questions: List of questions to rerank
            score_threshold: Minimum score threshold
            quality_threshold: Minimum quality threshold
            
        Returns:
            Reranked list of questions
        """
        if not questions:
            return []
        
        # Score questions (use existing score field or calculate)
        scored_questions = []
        for q in questions:
            # Use existing score if available, otherwise default to 5.0
            score = getattr(q, 'score', None) or 5.0
            
            # Calculate quality score based on question properties
            quality_score = self._calculate_quality_score(q)
            
            # Combined score
            combined_score = (score * alpha) + (quality_score * beta)
            
            if combined_score >= score_threshold and quality_score >= quality_threshold:
                scored_questions.append((combined_score, q))
        
        # Sort by combined score (descending)
        scored_questions.sort(key=lambda x: x[0], reverse=True)
        
        # Return questions only
        return [q for _, q in scored_questions]
    
    def _calculate_quality_score(self, question: QuizQuestion) -> float:
        """Calculate quality score for a question"""
        score = 0.25  # Base score
        
        # Check question length (not too short, not too long)
        q_len = len(question.question.split())
        if 8 <= q_len <= 200:
            score += 0.2
        
        # Check explanation exists
        if question.explanation and len(question.explanation.split()) > 10:
            score += 0.25
        
        # Check correct answer exists
        if question.correct_answer:
            score += 0.3
        
        return min(1.0, score)
    
    
    REFINE_BATCH_SIZE = 5

    async def _refine_batch(
        self,
        batch: List[Tuple[QuizQuestion, Optional[str]]]
    ) -> List[QuizQuestion]:
        """Refine a batch of (question, chunk) pairs. Chunk is None for AI-knowledge questions."""
        if not batch:
            return []
        questions_data = []
        for q, chunk in batch:
            q_dict = q.model_dump() if hasattr(q, 'model_dump') else dict(q)
            q_str = json.dumps(q_dict, default=str)
            if chunk:
                questions_data.append(f"Question:\n{q_str}\n\nSource chunk:\n{chunk[:1500]}")
            else:
                questions_data.append(f"Question:\n{q_str}")
        prompt = "Refine these quiz questions for higher quality. Return refined questions in the same order.\n\n" + "\n\n---\n\n".join(questions_data)
        try:
            result = await self._refine_agent.run(prompt)
            refined = result.output if hasattr(result, 'output') else []
            if len(refined) != len(batch):
                return [b[0] for b in batch]
            for i, (orig, _) in enumerate(batch):
                if i < len(refined):
                    r = refined[i]
                    if hasattr(orig, 'question_id') and orig.question_id:
                        r.question_id = orig.question_id
                    if hasattr(orig, 'chunk_index'):
                        r.chunk_index = orig.chunk_index
            return refined
        except Exception:
            return [b[0] for b in batch]

    async def refine_reranked_questions(
        self,
        questions: List[QuizQuestion],
        text_chunks: Optional[Union[List[str], Dict[int, str]]] = None
    ) -> List[QuizQuestion]:
        """
        Refine questions using a sub-agent. With chunks: refine against source.
        Without chunks: clean and improve. Runs parallel API calls (n per batch).
        text_chunks: list of contents (index=chunk_index) or dict chunk_index->content.
        """
        if not questions:
            return []
        chunk_map: Dict[int, str] = {}
        if isinstance(text_chunks, dict):
            chunk_map = text_chunks
        elif isinstance(text_chunks, list):
            chunk_map = {i: c for i, c in enumerate(text_chunks)}
        pairs: List[Tuple[QuizQuestion, Optional[str]]] = []
        for i, q in enumerate(questions):
            if not hasattr(q, 'question_id') or not q.question_id:
                q.question_id = f"q_{i+1}_{uuid.uuid4()}"
            if not hasattr(q, 'difficulty_level') or not q.difficulty_level:
                q.difficulty_level = DifficultyLevel.Medium
            chunk = chunk_map.get(getattr(q, 'chunk_index', -1)) if chunk_map else None
            pairs.append((q, chunk))
        batches = [
            pairs[j:j + self.REFINE_BATCH_SIZE]
            for j in range(0, len(pairs), self.REFINE_BATCH_SIZE)
        ]
        results = await asyncio.gather(*[self._refine_batch(b) for b in batches], return_exceptions=True)
        refined = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                refined.extend(b[0] for b in batches[i])
            else:
                refined.extend(r)
        order_map = {getattr(q, 'question_id', f"_{i}"): i for i, q in enumerate(questions)}
        refined.sort(key=lambda q: order_map.get(getattr(q, 'question_id', ''), 999))
        return refined[:len(questions)]
    
    async def _parse_document(
        self,
        text_content: Optional[str] = None,
        from_vector_db: bool = False,
        file_path: Optional[str] = None,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chunk_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Parse document and return chunks.
        
        Args:
            text_content: Raw text content
            from_vector_db: Whether to retrieve from vector DB
            file_path: Path to file
            document_id: Document ID
            chunk_size: Chunk size in words
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        doc_processor = get_document_processor()
        chunks = []
        
        try:
            if from_vector_db and document_id:
                results = await doc_processor.get_chunks_for_document(document_id, top_k=100)
                for i, result in enumerate(results):
                    chunks.append({
                        "content": result.get("content", ""),
                        "chunk_index": result.get("chunk_index", i),
                        "metadata": result
                    })
            elif text_content:
                # Chunk text content directly
                words = text_content.split()
                current_chunk = []
                current_index = 0
                
                for word in words:
                    current_chunk.append(word)
                    if len(current_chunk) >= chunk_size:
                        chunks.append({
                            "content": " ".join(current_chunk),
                            "chunk_index": current_index,
                            "metadata": {}
                        })
                        current_chunk = []
                        current_index += 1
                
                # Add remaining words
                if current_chunk:
                    chunks.append({
                        "content": " ".join(current_chunk),
                        "chunk_index": current_index,
                        "metadata": {}
                    })
            elif file_path:
                file_name = os.path.basename(file_path)
                db = get_database_service()
                doc = await db.get_document_by_file_name(file_name, user_id)
                if doc and doc.get("pinecone_index_name"):
                    doc_id = doc.get("id")
                    results = await doc_processor.get_chunks_for_document(doc_id, top_k=100)
                    for i, result in enumerate(results):
                        chunks.append({
                            "content": result.get("content", ""),
                            "chunk_index": result.get("chunk_index", i),
                            "metadata": result
                        })
        
        except Exception as e:
            print(f"Error parsing document: {e}")
        
        return chunks
    
    async def score_open_ended_answer(
        self,
        question: QuizQuestion,
        user_answer: str,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        provider: str = "google"
    ) -> OpenEndedAnswer:
        """
        Score an open-ended answer using AI.
        
        This is used for quiz mode open-ended questions.
        For game_master open-ended answers, use _analyze_performance in game_v2.py
        
        Args:
            question: The quiz question
            user_answer: User's answer
            model_name: Optional model name override
            api_key: Optional API key override
            provider: Model provider
            
        Returns:
            OpenEndedAnswer with score and feedback
        """
        # Initialize scoring agent if not exists or if model changed
        if self.scoring_agent is None or model_name or api_key:
            scoring_model = get_quiz_model(
                model_name or self.model_name,
                api_key or self.api_key,
            )
            self.scoring_agent = Agent(
                scoring_model,
                system_prompt="""
                You are a medical education evaluator. Score open-ended quiz answers on a scale of 0-10.
                Provide detailed feedback, identify strengths and weaknesses.
                Be fair but thorough. Reward partial understanding and penalize significant errors.
                """,
                output_type=OpenEndedAnswer
            )
        
        prompt = f"""
        Evaluate this open-ended quiz answer:
        
        Question: {question.question}
        Correct Answer/Model Answer: {question.correct_answer}
        User Answer: {user_answer}
        Explanation: {question.explanation or "N/A"}
        
        Score the answer (0-10) and provide:
        1. Overall score
        2. Detailed feedback
        3. List of strengths
        4. List of weaknesses
        
        Be fair but thorough. Reward partial understanding and penalize significant errors.
        """
        
        try:
            result = await self.scoring_agent.run(prompt)
            scored_answer = result.output if hasattr(result, 'output') else result
            
            # Ensure it's an OpenEndedAnswer object
            if isinstance(scored_answer, dict):
                return OpenEndedAnswer(**scored_answer)
            elif isinstance(scored_answer, OpenEndedAnswer):
                return scored_answer
            else:
                raise ValueError("Agent did not return valid OpenEndedAnswer")
        except Exception as e:
            # Fallback: return default score
            return OpenEndedAnswer(
                score=5.0,
                feedback=f"Error scoring answer: {str(e)}",
                strengths=[],
                weaknesses=["Unable to evaluate answer due to technical error"]
            )
    
    def generate_prompt(
        self,
        quiz_type: str,
        num_questions: int,
        num_multiple_choice: int,
        num_true_false: int,
        num_open_ended: int,
        time_limit: int,
        difficulty_level: Optional[DifficultyLevel],
        user_subject_of_study: str,
        context: Optional[str] = None
    ) -> str:
        """
        Generate prompt for quiz generation.
        
        Args:
            quiz_type: Type of quiz
            num_questions: Total number of questions
            num_multiple_choice: Number of multiple choice questions
            num_true_false: Number of true/false questions
            num_open_ended: Number of open-ended questions
            time_limit: Time limit per question
            difficulty_level: Difficulty level
            user_subject_of_study: Subject/field of study
            context: Additional context
            
        Returns:
            Formatted prompt string
        """
        if context:
            instruction = f"{context}\n\nGiven the document/content above, generate medical questions with the following specifications:"
        else:
            instruction = "Generate medical questions with the following specifications:"
        
        return f"""
        {instruction}
        
        - Type: {quiz_type}
        - Total Questions: {num_questions}
        - Multiple Choice: {num_multiple_choice}
        - True/False: {num_true_false}
        - Open-ended (Theory): {num_open_ended}
        - Time limit: {time_limit} seconds per question
        - Difficulty level: {difficulty_level or DifficultyLevel.Medium}
        - User Field/subject of study: {user_subject_of_study}
        - Focus on medical knowledge appropriate for field/subject of study
        
        For multiple choice questions:
        - Provide exactly 4-5 options (options should be relevant to the question)
        - Only one correct answer
        - Include clear explanations
        
        For true/false questions:
        - Provide exactly 2 options (True/False)
        - Only one correct answer
        - Include clear explanations
        
        For open-ended questions:
        - Require detailed explanations
        - Test critical thinking and application
        - Include model answers for scoring
        
        Create engaging, educational questions that test both theoretical knowledge and practical application.
        Assign a score (0-10) to each question based on its importance for fundamental understanding.
        """


# Global instance
_quiz_agent_instance: Optional[QuizAgent] = None


def get_quiz_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google",
    use_internet: bool = True
) -> QuizAgent:
    """Get or create the global Quiz Agent instance"""
    global _quiz_agent_instance
    if _quiz_agent_instance is None:
        _quiz_agent_instance = QuizAgent(model_name, api_key, provider, use_internet)
    return _quiz_agent_instance


# Standalone functions for backward compatibility
async def generate_quiz(
    quiz_type: str = "general",
    num_questions: int = 10,
    time_limit: int = 600,
    context: Optional[str] = None,
    source: str = "ai_knowledge",
    num_multiple_choice: Optional[int] = None,
    num_open_ended: Optional[int] = None,
    num_true_false: Optional[int] = None,
    user_subject_of_study: Optional[str] = None,
    document_id: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google",
    use_internet: bool = True
) -> Quiz:
    """
    Standalone function to generate quiz (for backward compatibility).
    
    This function uses the QuizAgent class internally.
    """
    agent = get_quiz_agent(model_name, api_key, provider, use_internet)
    
    return await agent.generate_quiz(
        from_document=(source == "document"),
        document_id=document_id,
        num_questions=num_questions,
        quiz_type=quiz_type,
        user_subject_of_study=user_subject_of_study or "general medicine",
        time_limit=time_limit,
        context=context,
        num_multiple_choice=num_multiple_choice,
        num_open_ended=num_open_ended,
        num_true_false=num_true_false
    )


async def score_open_ended_answer(
    question: QuizQuestion,
    user_answer: str,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> OpenEndedAnswer:
    """
    Standalone function to score open-ended answer (for backward compatibility).
    
    This function uses the QuizAgent class internally.
    """
    agent = get_quiz_agent(model_name, api_key, provider)
    return await agent.score_open_ended_answer(question, user_answer, model_name, api_key, provider)
