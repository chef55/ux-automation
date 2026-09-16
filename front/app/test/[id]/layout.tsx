//import "../../globals.css";

import Footer from "@/app/Footer";

export default function TestLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <Footer></Footer>
      </body>
    </html>
  );
}
