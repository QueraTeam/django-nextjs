import { Html, Head, Main, NextScript } from "next/document";
import Link from "next/link";

export default function Document() {
  return (
    <Html>
      <Head />
      <body id="__django_nextjs_body">
        <div id="__django_nextjs_body_begin" />

        <nav style={{ background: "gray" }}>
          <h1>page router</h1>
          <Link href="/app">Go to App</Link>
          <br />
          <Link href="/page">Go to Page</Link>
        </nav>

        <Main />
        <NextScript />
        <div id="__django_nextjs_body_end" />
      </body>
    </Html>
  );
}
