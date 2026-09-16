import { useContext, useEffect, useState } from "react";
import "./globals.css";
import axios from "axios";
import { AuthContext } from "./AuthContext";
export default function Header() {

  const auth = useContext(AuthContext)
  
  return (
    <header className="fixed w-full flex bg-background text-1.5xl items-center justify-between px-3 border-b-2 [border-image:var(--grad)_1]">
        <div className="flex gap-5 items-center">
          <a href="/" className="header-logo text-3xl h-full p-2 hover:underline">UXLab</a>
          <a href="/test/new" className="header-button h-full p-2 hover:bg-[--bg-1] transition-colors">Создать тестирование</a>
          <a href="/user" className="header-login h-full p-2 hover:bg-[--bg-1] transition-colors">История</a>
        </div>
        {auth === '' ? <a href="/auth" className="header-user hover:bg-[--bg-1] transition-colors p-2">Войти</a> : <a href="/user" className="header-user hover:bg-[--bg-1] transition-colors p-2">{auth}</a>}
    </header>
  );
}
