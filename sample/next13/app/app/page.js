import Link from "next/link";

export default function Home() {
  return (
    <div>
      <div>/app</div>
      <Link href="/app/second">Go To /app/second</Link>
    </div>
  );
}
