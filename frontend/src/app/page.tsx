import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: "2rem" }}>
      <h1>A7 Disruption Router</h1>
      <p>Grounded exception routing for logistics disruptions.</p>
      <nav style={{ marginTop: "1rem" }}>
        <Link href="/reviews" style={{ color: "#0066cc" }}>
          Review queue →
        </Link>
      </nav>
    </main>
  );
}
