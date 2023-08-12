import Link from "next/link";

export default function Home() {
  return (
    <div>
      <div>/app</div>
      <Link href="/app/second" id="2">
        /app/second
      </Link>
    </div>
  );
}
