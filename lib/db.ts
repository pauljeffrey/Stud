// This is a placeholder for database integration
// In a real app, you would use a proper database like PostgreSQL, MongoDB, etc.

import type { User, GameState } from "./types"

// Mock database using in-memory storage
// In a real app, this would be replaced with actual database calls
class MockDatabase {
  private users: Map<string, User> = new Map()
  private gameStates: Map<string, GameState[]> = new Map()

  // User methods
  async createUser(user: Omit<User, "id">): Promise<User> {
    const id = Math.random().toString(36).substring(2, 15)
    const newUser = { ...user, id }
    this.users.set(id, newUser)
    return newUser
  }

  async getUserById(id: string): Promise<User | null> {
    return this.users.get(id) || null
  }

  async getUserByEmail(email: string): Promise<User | null> {
    for (const user of this.users.values()) {
      if (user.email === email) {
        return user
      }
    }
    return null
  }

  // Game state methods
  async saveGameState(gameState: GameState): Promise<void> {
    const userStates = this.gameStates.get(gameState.userId) || []
    userStates.push(gameState)
    this.gameStates.set(gameState.userId, userStates)
  }

  async getGameStates(userId: string): Promise<GameState[]> {
    return this.gameStates.get(userId) || []
  }

  async getLatestGameState(userId: string): Promise<GameState | null> {
    const states = this.gameStates.get(userId) || []
    if (states.length === 0) return null

    // Sort by timestamp (assuming the most recent is last)
    return states[states.length - 1]
  }
}

// Export a singleton instance
export const db = new MockDatabase()

