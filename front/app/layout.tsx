"use client"
import { useEffect, useState } from "react";
import Footer from "./Footer";
import "./globals.css";
import Header from "./Header";
import axios from "axios";
import { AuthContext, AuthIdContext } from "./AuthContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
    const [auth, setAuth] = useState('')
    const [id, setId] = useState(-1)

    useEffect(() => {
    axios.get('http://localhost:3001/auth', {withCredentials:true})
      .then(res =>{setId(res.data.id); setAuth(res.data.username)})
      .catch(err => {
        setId(-1)
        setAuth('')
      });
  }, []);

  return (
    <html
      lang="en"
      className={`h-full antialiased`}
    >
      <body className="flex flex-col min-h-full">
        <AuthIdContext value={id}>
        <AuthContext value={auth}>

          <Header></Header>
          {children}
          
        </AuthContext>
        </AuthIdContext>
      </body>
    </html>
  );
}
