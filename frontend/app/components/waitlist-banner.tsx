import Link from "next/link"

const MESSAGE =
  "🚀 Want to be first in line when Stud launches — and help shape early pricing? Join the waitlist →"

export default function WaitlistBanner() {
  return (
    <Link
      href="/waitlist"
      aria-label="Join the Stud waitlist"
      className="fixed top-0 left-0 right-0 z-[60] h-9 overflow-hidden bg-gradient-to-r from-purple-800 via-purple-700 to-blue-800 text-white text-sm border-b border-purple-500/40"
    >
      <div className="waitlist-marquee-track flex h-full items-center whitespace-nowrap">
        {[0, 1].map((block) => (
          <span key={block} className="flex items-center" aria-hidden={block === 1}>
            {Array.from({ length: 8 }).map((_, i) => (
              <span key={i} className="mx-8">
                {MESSAGE}
              </span>
            ))}
          </span>
        ))}
      </div>
    </Link>
  )
}
