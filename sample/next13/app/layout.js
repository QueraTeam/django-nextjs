import { headers } from "next/headers";
import Link from "next/link";

export default function RootLayout({ children }) {
  const headersList = headers();
  const preBody = headersList.get("pre_body");
  const postBody = headersList.get("post_body");

  return (
    <html lang="en">
      <body id="__django_nextjs_body">
        <div dangerouslySetInnerHTML={{ __html: preBody }} />
        <nav style={{ background: "gray" }}>
          <h1>app router</h1>
          <Link href="/app">Go to App</Link>
          <br />
          <Link href="/page">Go to Page</Link>
        </nav>
        {children}
        <div dangerouslySetInnerHTML={{ __html: postBody }} />
      </body>
    </html>
  );
}
