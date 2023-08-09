import Head from "next/head";
import { headers } from "next/headers";
import Link from "next/link";

export default function RootLayout({ children }) {
  const headers_ = headers();

  return (
    <html lang="en">
      <body id="__django_nextjs_body">
        <div dangerouslySetInnerHTML={{ __html: headers_.get("dj_pre_body") }} />
        <nav style={{ background: "gray" }}>
          <h1>app router</h1>
          <Link href="/app">Go to App</Link>
          <br />
          <Link href="/page">Go to Page</Link>
        </nav>
        {children}
        <div dangerouslySetInnerHTML={{ __html: headers_.get("dj_post_body") }} />
      </body>
    </html>
  );
}
