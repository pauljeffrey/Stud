import { proxy } from "@/app/lib/proxy"

export const DELETE = async (
  req: Request,
  context: { params: Promise<{ quizId: string }> }
) => {
  const { quizId } = await context.params
  return proxy(req, `/api/quiz/saved/${quizId}`, { method: "DELETE" })
}
