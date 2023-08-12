import Link from "next/link";

export default function Page() {
  return (
    <div>
      <div>/page</div>
      <Link href="/page/second">Go To /page/second</Link>
    </div>
  );
}
