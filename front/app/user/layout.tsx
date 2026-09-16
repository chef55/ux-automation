import Footer from "../Footer";
import "../globals.css";
import Header from "../Header";

export default function UserLayout({
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
