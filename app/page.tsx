import type React from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Stethoscope, Users, Brain } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-900 to-purple-700 text-white">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="flex flex-col items-center text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6">MediQuest</h1>
          <p className="text-xl md:text-2xl mb-10 max-w-3xl">
            An immersive medical role-playing experience where you diagnose, treat, and save lives
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link href="/demo">
              <Button size="lg" className="bg-purple-500 hover:bg-purple-600">
                Try Demo <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/auth/register">
              <Button size="lg" variant="outline" className="border-purple-400 text-white hover:bg-purple-800">
                Register Now
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-purple-800 py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold mb-12 text-center">Game Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Stethoscope className="h-12 w-12 mb-4" />}
              title="Medical Challenges"
              description="Diagnose patients, perform surgeries, and handle medical emergencies in realistic scenarios"
            />
            <FeatureCard
              icon={<Users className="h-12 w-12 mb-4" />}
              title="Multiplayer Experience"
              description="Play solo or collaborate with other medical professionals to solve complex cases"
            />
            <FeatureCard
              icon={<Brain className="h-12 w-12 mb-4" />}
              title="AI Game Master"
              description="Interact with an intelligent Game Master that adapts scenarios based on your decisions"
            />
          </div>
        </div>
      </div>

      {/* How to Play Section */}
      <div className="container mx-auto px-4 py-16">
        <h2 className="text-3xl md:text-4xl font-bold mb-8 text-center">How to Play</h2>
        <div className="max-w-3xl mx-auto">
          <ol className="space-y-6">
            <li className="flex gap-4">
              <div className="bg-purple-500 rounded-full h-8 w-8 flex items-center justify-center flex-shrink-0 mt-1">
                1
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Choose Your Specialty</h3>
                <p>
                  Select your medical profession - from General Practitioner to Neurosurgeon - each with unique
                  abilities.
                </p>
              </div>
            </li>
            <li className="flex gap-4">
              <div className="bg-purple-500 rounded-full h-8 w-8 flex items-center justify-center flex-shrink-0 mt-1">
                2
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Diagnose & Treat</h3>
                <p>
                  Analyze symptoms, order tests, and collaborate with other specialists to determine the best treatment
                  plan.
                </p>
              </div>
            </li>
            <li className="flex gap-4">
              <div className="bg-purple-500 rounded-full h-8 w-8 flex items-center justify-center flex-shrink-0 mt-1">
                3
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2">Handle Emergencies</h3>
                <p>React quickly to medical emergencies and make critical decisions under pressure.</p>
              </div>
            </li>
          </ol>
          <div className="mt-10 text-center">
            <Link href="/auth/login">
              <Button size="lg" className="bg-purple-500 hover:bg-purple-600">
                Start Playing Now
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="bg-purple-700 p-6 rounded-lg text-center">
      <div className="flex justify-center">{icon}</div>
      <h3 className="text-xl font-bold mb-3">{title}</h3>
      <p>{description}</p>
    </div>
  )
}
