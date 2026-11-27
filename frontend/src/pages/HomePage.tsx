import { FeatureCards } from './home/FeatureCards'
import { HomeFooter } from './home/HomeFooter'
import { HomeHero } from './home/HomeHero'
import { HomeNav } from './home/HomeNav'
import { Principles } from './home/Principles'
import { PricingCards } from './home/PricingCards'
import { StudentSteps } from './home/StudentSteps'
import { TeacherBand } from './home/TeacherBand'
import { useReveal } from './home/useReveal'
import '../styles/home.css'
import '../styles/home-sections.css'

/** 시작 화면(스크롤): 히어로 → 기능 → 교수자 → 학생 → 원칙 → 요금제 → 푸터 */
export default function HomePage() {
  useReveal()
  return (
    <>
      <HomeNav />
      <main>
        <HomeHero />
        <FeatureCards />
        <TeacherBand />
        <StudentSteps />
        <Principles />
        <PricingCards />
      </main>
      <HomeFooter />
    </>
  )
}
