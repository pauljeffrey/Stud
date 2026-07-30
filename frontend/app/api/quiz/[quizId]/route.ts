import { proxy } from "@/app/lib/proxy"

export const GET = async (
  req: Request,
  context: { params: Promise<{ quizId: string }> }
) => {
  const { quizId } = await context.params
  return proxy(req, `/api/quiz/${quizId}`)
}
