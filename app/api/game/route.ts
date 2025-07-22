import { NextResponse } from "next/server"

// This is a placeholder for the AI service integration
// In a real app, you would connect to your FastAPI service
export async function POST(request: Request) {
  try {
    const { prompt, gameState } = await request.json()

    // In a production app, this would call your FastAPI endpoint
    // const response = await fetch('http://your-fastapi-url/api/generate-response', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ prompt, gameState }),
    // });
    // const data = await response.json();

    // For now, simulate AI response
    const aiResponse = simulateAIResponse(prompt, gameState)

    return NextResponse.json(aiResponse)
  } catch (error) {
    console.error("Game AI error:", error)
    return NextResponse.json({ success: false, message: "Server error" }, { status: 500 })
  }
}

// Placeholder function to simulate AI responses
function simulateAIResponse(prompt: string, gameState: any) {
  // This would be replaced by your actual AI service
  const lowerPrompt = prompt.toLowerCase()
  const caseId = gameState?.caseId || "case1"

  if (caseId === "case1") {
    if (lowerPrompt.includes("ecg") || lowerPrompt.includes("ekg")) {
      return {
        text: "The ECG shows ST-segment elevation in leads II, III, and aVF, suggesting an inferior wall myocardial infarction.",
        image: "/placeholder.svg?height=300&width=500",
        actions: ["Administer medication", "Order additional tests", "Consult specialist"],
      }
    } else if (lowerPrompt.includes("treat") || lowerPrompt.includes("medication")) {
      return {
        text: "You administer aspirin 325mg and nitroglycerin. The patient's pain begins to subside slightly, but they still require urgent intervention.",
        actions: ["Consult with cardiology", "Prepare for catheterization", "Monitor vital signs"],
      }
    }
  } else if (caseId === "case2") {
    if (lowerPrompt.includes("ct") || lowerPrompt.includes("scan")) {
      return {
        text: "The CT scan reveals subarachnoid hemorrhage, likely due to a ruptured aneurysm. This is a medical emergency requiring immediate neurosurgical consultation.",
        image: "/placeholder.svg?height=300&width=500",
        actions: ["Consult neurosurgery", "Prepare for surgery", "Administer medication"],
      }
    }
  }

  return {
    text: "The patient looks at you expectantly. What would you like to do next?",
    actions: ["Examine patient", "Order tests", "Begin treatment"],
  }
}
