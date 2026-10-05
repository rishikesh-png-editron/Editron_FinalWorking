import { Navbar } from "@/components/capgen/navbar";
import { Hero } from "@/components/capgen/hero";
import { CaptionStudio } from "@/components/capgen/caption-studio";
import { AutoTrim } from "@/components/capgen/auto-trim";
import { Stats } from "@/components/capgen/stats";
import { Templates } from "@/components/capgen/templates";
import { Pricing } from "@/components/capgen/pricing";
import { Testimonials } from "@/components/capgen/testimonials";
import { Faq } from "@/components/capgen/faq";
import { FinalCta } from "@/components/capgen/final-cta";
import { Footer } from "@/components/capgen/footer";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <main className="flex-1">
        <Hero />
        <CaptionStudio />
        <AutoTrim />
        <Stats />
        <Templates />
        <Pricing />
        <Testimonials />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
    </div>
  );
}
