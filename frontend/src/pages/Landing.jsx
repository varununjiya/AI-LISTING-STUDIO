import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { ReactLenis } from "lenis/react";
import Marquee from "react-fast-marquee";
import { useNavigate } from "react-router-dom";
import {
  ArrowUpRight,
  Sparkles,
  Boxes,
  ScanLine,
  Wand2,
  FileSpreadsheet,
  Moon,
  Sun,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";
import { startGoogleLogin } from "@/lib/auth";

const IMG = {
  abstract:
    "https://images.unsplash.com/photo-1710244182004-1c708b3f146d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NzV8MHwxfHNlYXJjaHwyfHx0cmVuZHklMjBnZW4lMjB6JTIwYWJzdHJhY3QlMjAzZCUyMHNoYXBlfGVufDB8fHx8MTc4MzkzMzg3NHww&ixlib=rb-4.1.0&q=85",
  sneaker1:
    "https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwxfHxmbG9hdGluZyUyMHNuZWFrZXJzJTIwcHJvZHVjdCUyMHBob3RvZ3JhcGh5JTIwc3R1ZGlvfGVufDB8fHx8MTc4MzkzMzg3NHww&ixlib=rb-4.1.0&q=85",
  sneaker2:
    "https://images.unsplash.com/photo-1560769629-975ec94e6a86?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwyfHxmbG9hdGluZyUyMHNuZWFrZXJzJTIwcHJvZHVjdCUyMHBob3RvZ3JhcGh5JTIwc3R1ZGlvfGVufDB8fHx8MTc4MzkzMzg3NHww&ixlib=rb-4.1.0&q=85",
  dashboard:
    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwxfHxlY29tbWVyY2UlMjBkYXNoYm9hcmQlMjBsYXB0b3AlMjBzZXR1cHxlbnwwfHx8fDE3ODM5MzM4NzR8MA&ixlib=rb-4.1.0&q=85",
};

const HERO_LINES = ["Listings that", "outsmart the", "algorithm."];

function LineReveal({ children, delay = 0 }) {
  return (
    <span className="block overflow-hidden">
      <motion.span
        className="block"
        initial={{ y: "110%" }}
        animate={{ y: 0 }}
        transition={{ duration: 0.9, delay, ease: [0.22, 1, 0.36, 1] }}
      >
        {children}
      </motion.span>
    </span>
  );
}

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] } },
};

function Nav() {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="fixed top-0 inset-x-0 z-50">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 py-4">
        <div className="flex items-center justify-between rounded-full glass bg-background/60 border border-border px-5 py-2.5">
          <a href="/" className="flex items-center gap-2" data-testid="landing-logo">
            <div className="h-8 w-8 rounded-lg bg-accent flex items-center justify-center">
              <Boxes className="h-5 w-5 text-accent-foreground" />
            </div>
            <span className="font-heading font-extrabold text-sm tracking-tight">
              AI&nbsp;LISTING&nbsp;STUDIO
            </span>
          </a>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium">
            <a href="#how" className="hover:text-accent transition-colors" data-testid="nav-how">How it works</a>
            <a href="#showcase" className="hover:text-accent transition-colors" data-testid="nav-showcase">Showcase</a>
            <a href="#pricing" className="hover:text-accent transition-colors" data-testid="nav-pricing">Pricing</a>
          </nav>
          <div className="flex items-center gap-2">
            <button
              onClick={toggleTheme}
              data-testid="landing-theme-toggle"
              className="h-9 w-9 rounded-full border border-border flex items-center justify-center hover:bg-secondary transition-colors"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <Button
              data-testid="landing-login-btn"
              onClick={() => (user ? navigate("/dashboard") : startGoogleLogin())}
              className="rounded-full font-semibold"
            >
              {user ? "Dashboard" : "Sign in"}
              <ArrowUpRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y1 = useTransform(scrollYProgress, [0, 1], [0, -120]);
  const y2 = useTransform(scrollYProgress, [0, 1], [0, 160]);
  const rot = useTransform(scrollYProgress, [0, 1], [0, 40]);
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <section ref={ref} className="relative min-h-screen flex flex-col justify-center overflow-hidden pt-28 grain">
      {/* floating 3D shapes */}
      <motion.img
        src={IMG.abstract}
        style={{ y: y1, rotate: rot }}
        className="pointer-events-none select-none absolute -right-10 top-24 w-[42vw] max-w-[560px] rounded-[2rem] object-cover opacity-90 animate-float-slow hidden sm:block"
        alt=""
      />
      <motion.div
        style={{ y: y2 }}
        className="pointer-events-none absolute -left-24 bottom-10 h-72 w-72 rounded-full bg-accent/30 blur-3xl"
      />
      <motion.div
        style={{ y: y1 }}
        className="pointer-events-none absolute right-1/3 top-1/4 h-56 w-56 rounded-full bg-primary/20 blur-3xl"
      />

      <div className="relative z-10 mx-auto max-w-7xl w-full px-5 sm:px-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-background/50 glass px-4 py-1.5 text-xs font-bold uppercase tracking-widest mb-8"
        >
          <Sparkles className="h-3.5 w-3.5 text-accent" />
          AI product listings for Amazon &amp; Flipkart
        </motion.div>

        <h1 className="font-heading font-black leading-[0.92] tracking-tighter text-5xl sm:text-7xl lg:text-8xl max-w-5xl">
          {HERO_LINES.map((line, i) => (
            <LineReveal key={line} delay={0.15 + i * 0.12}>
              {i === 2 ? <span className="text-accent">{line}</span> : line}
            </LineReveal>
          ))}
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.7 }}
          className="mt-8 max-w-xl text-base sm:text-lg text-muted-foreground text-balance"
        >
          Turn raw product specs into conversion-ready titles, bullet points, SEO
          keywords and marketplace-perfect descriptions — in one click.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.85, duration: 0.7 }}
          className="mt-10 flex flex-wrap items-center gap-4"
        >
          <Button
            data-testid="hero-cta-btn"
            size="lg"
            onClick={() => (user ? navigate("/dashboard") : startGoogleLogin())}
            className="rounded-full h-14 px-8 text-base font-semibold group"
          >
            Start generating — it&apos;s free
            <ArrowUpRight className="ml-1 h-5 w-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Button>
          <a
            href="#how"
            className="text-sm font-semibold underline underline-offset-4 decoration-muted-foreground hover:decoration-accent"
            data-testid="hero-secondary-link"
          >
            See how it works
          </a>
        </motion.div>
      </div>
    </section>
  );
}

function MarqueeStrip() {
  return (
    <div className="border-y border-border py-6 bg-background overflow-hidden">
      <Marquee speed={40} gradient={false}>
        {Array.from({ length: 6 }).map((_, i) => (
          <span key={i} className="flex items-center gap-8 mx-8">
            <span className="font-heading font-black text-4xl sm:text-6xl text-outline">AMAZON</span>
            <span className="h-3 w-3 rounded-full bg-accent" />
            <span className="font-heading font-black text-4xl sm:text-6xl">FLIPKART</span>
            <span className="h-3 w-3 rounded-full bg-primary" />
            <span className="font-heading font-black text-4xl sm:text-6xl text-outline">AI&nbsp;GENERATION</span>
            <span className="h-3 w-3 rounded-full bg-accent" />
          </span>
        ))}
      </Marquee>
    </div>
  );
}

const CHAPTERS = [
  {
    n: "01",
    title: "Drop in your product",
    body: "Brand, material, dimensions, price — fill the form or bulk-upload a spreadsheet. Your catalog, structured.",
    icon: Boxes,
    img: IMG.sneaker1,
  },
  {
    n: "02",
    title: "AI reads the algorithm",
    body: "Our engine studies marketplace ranking signals and writes copy that search actually rewards.",
    icon: ScanLine,
    img: IMG.sneaker2,
  },
  {
    n: "03",
    title: "Review & refine",
    body: "Every field is editable. Copy, regenerate or fine-tune section by section until it's perfect.",
    icon: Wand2,
    img: IMG.dashboard,
  },
  {
    n: "04",
    title: "Export & publish",
    body: "One click to Amazon, Flipkart or generic .xlsx — formatted exactly how each marketplace expects.",
    icon: FileSpreadsheet,
    img: IMG.abstract,
  },
];

function Manifesto() {
  return (
    <section id="how" className="mx-auto max-w-7xl px-5 sm:px-8 py-24 sm:py-32">
      <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-100px" }}>
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-4">The workflow</p>
        <h2 className="font-heading font-black text-4xl sm:text-5xl tracking-tight max-w-3xl">
          Four moves from raw specs to ranking listings.
        </h2>
      </motion.div>

      <div className="mt-16 space-y-24 sm:space-y-32">
        {CHAPTERS.map((c, i) => (
          <motion.div
            key={c.n}
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-120px" }}
            className={`grid lg:grid-cols-2 gap-10 lg:gap-16 items-center ${i % 2 ? "lg:[direction:rtl]" : ""}`}
          >
            <div className="[direction:ltr]">
              <div className="flex items-center gap-4 mb-6">
                <span className="font-heading font-black text-6xl sm:text-7xl text-outline">{c.n}</span>
                <c.icon className="h-8 w-8 text-accent" />
              </div>
              <h3 className="font-heading font-bold text-2xl sm:text-3xl mb-4">{c.title}</h3>
              <p className="text-muted-foreground text-base sm:text-lg max-w-md">{c.body}</p>
            </div>
            <div className="[direction:ltr] relative">
              <div className="absolute -inset-4 bg-accent/20 blur-3xl rounded-full" />
              <div className="relative aspect-[4/3] overflow-hidden rounded-[1.75rem] border border-border">
                <img src={c.img} alt={c.title} className="h-full w-full object-cover" />
                <div className="absolute inset-0 ring-1 ring-inset ring-white/10 rounded-[1.75rem]" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function Showcase() {
  const bullets = [
    "PREMIUM LEATHER: Full-grain finish built to last.",
    "ALL-DAY COMFORT: Cushioned sole, breathable lining.",
    "VERSATILE STYLE: Pairs with everything you own.",
  ];
  const keywords = ["running shoes", "premium sneakers", "leather trainers", "gym footwear", "unisex shoes"];
  return (
    <section id="showcase" className="mx-auto max-w-7xl px-5 sm:px-8 py-24">
      <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="mb-12">
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-4">Under the hood</p>
        <h2 className="font-heading font-black text-4xl sm:text-5xl tracking-tight max-w-3xl">
          Everything a marketplace listing needs.
        </h2>
      </motion.div>

      <div className="grid md:grid-cols-3 gap-5">
        <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="md:col-span-2 rounded-3xl border border-border bg-card p-8">
          <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground mb-6">Amazon bullet points</p>
          <ul className="space-y-4">
            {bullets.map((b) => (
              <li key={b} className="flex gap-3 items-start">
                <span className="mt-1 h-2 w-2 rounded-full bg-accent shrink-0" />
                <span className="font-medium">{b}</span>
              </li>
            ))}
          </ul>
        </motion.div>
        <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="rounded-3xl border border-border bg-primary text-primary-foreground p-8 flex flex-col justify-between">
          <p className="font-mono text-xs uppercase tracking-widest opacity-80 mb-6">SEO keywords</p>
          <div className="flex flex-wrap gap-2">
            {keywords.map((k) => (
              <span key={k} className="rounded-full bg-background/20 px-3 py-1 text-sm font-medium">{k}</span>
            ))}
          </div>
        </motion.div>
        <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="rounded-3xl border border-border bg-accent text-accent-foreground p-8">
          <p className="font-mono text-xs uppercase tracking-widest opacity-80 mb-2">Meta description</p>
          <p className="font-heading font-bold text-xl leading-snug">Shop premium leather sneakers. Comfort meets style. Best price online.</p>
        </motion.div>
        <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="md:col-span-2 rounded-3xl border border-border bg-card p-8">
          <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground mb-6">Product specifications</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-y-4 gap-x-8">
            {[["Brand", "Aether"], ["Material", "Full-grain leather"], ["Color", "Off-white"], ["Warranty", "1 Year"], ["Origin", "India"], ["HSN", "6403"]].map(([k, v]) => (
              <div key={k}>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">{k}</p>
                <p className="font-semibold">{v}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function Stats() {
  const stats = [
    ["10x", "faster listing creation"],
    ["2", "marketplaces, one workflow"],
    ["9", "AI-generated fields per product"],
    ["∞", "products, bulk generated"],
  ];
  return (
    <section className="border-y border-border">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 py-16 grid grid-cols-2 lg:grid-cols-4 gap-8">
        {stats.map(([num, label], i) => (
          <motion.div
            key={label}
            variants={fadeUp}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            transition={{ delay: i * 0.08 }}
          >
            <p className="font-heading font-black text-5xl sm:text-6xl tracking-tighter">{num}</p>
            <p className="text-sm text-muted-foreground mt-2">{label}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

function Pricing() {
  const { user } = useAuth();
  const navigate = useNavigate();
  return (
    <section id="pricing" className="mx-auto max-w-7xl px-5 sm:px-8 py-24 sm:py-32">
      <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }} className="rounded-[2.5rem] border border-border bg-card p-10 sm:p-16 text-center relative overflow-hidden grain">
        <div className="absolute -top-20 -right-20 h-72 w-72 rounded-full bg-accent/30 blur-3xl" />
        <p className="font-mono text-xs uppercase tracking-widest text-accent mb-6 relative">Ready when you are</p>
        <h2 className="font-heading font-black text-4xl sm:text-6xl tracking-tighter max-w-3xl mx-auto relative">
          Stop writing listings. Start shipping them.
        </h2>
        <p className="mt-6 text-muted-foreground max-w-xl mx-auto relative">
          Sign in with Google and generate your first AI listing in under a minute.
        </p>
        <Button
          data-testid="pricing-cta-btn"
          size="lg"
          onClick={() => (user ? navigate("/dashboard") : startGoogleLogin())}
          className="mt-10 rounded-full h-14 px-10 text-base font-semibold relative"
        >
          Get started free
          <ArrowUpRight className="ml-1 h-5 w-5" />
        </Button>
      </motion.div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border overflow-hidden">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 pt-16 pb-8">
        <div className="flex flex-col sm:flex-row justify-between gap-8 mb-12">
          <div className="max-w-xs">
            <div className="flex items-center gap-2 mb-4">
              <div className="h-8 w-8 rounded-lg bg-accent flex items-center justify-center">
                <Boxes className="h-5 w-5 text-accent-foreground" />
              </div>
              <span className="font-heading font-extrabold text-sm">AI LISTING STUDIO</span>
            </div>
            <p className="text-sm text-muted-foreground">
              AI-powered product listings for Amazon &amp; Flipkart sellers.
            </p>
          </div>
          <div className="flex gap-16 text-sm">
            <div className="space-y-3">
              <p className="font-mono text-xs uppercase tracking-widest text-muted-foreground">Product</p>
              <a href="#how" className="block hover:text-accent">How it works</a>
              <a href="#showcase" className="block hover:text-accent">Showcase</a>
              <a href="#pricing" className="block hover:text-accent">Pricing</a>
            </div>
          </div>
        </div>
        <div className="leading-none">
          <span className="font-heading font-black tracking-tighter text-[18vw] block text-outline select-none">
            AI STUDIO
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-6">© {new Date().getFullYear()} AI Listing Studio. All rights reserved.</p>
      </div>
    </footer>
  );
}

export default function Landing() {
  return (
    <ReactLenis root>
      <main className="bg-background text-foreground">
        <Nav />
        <Hero />
        <MarqueeStrip />
        <Manifesto />
        <Showcase />
        <Stats />
        <Pricing />
        <Footer />
      </main>
    </ReactLenis>
  );
}
