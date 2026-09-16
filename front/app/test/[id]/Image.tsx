'use client'
import axios from "axios";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
//import "../globals.css";

export default function Image(args:any) {
  return (
    <div  onClick={()=>{args.setOverlayId(args.image.id); args.setOverlayText(args.image.content)}} className=" mt-10 rounded-2xl block w-11/12 p-3 hover:bg-[var(--bg-3)] transition-colors cursor-pointer">
      <img src={'http://localhost:3001/image/'+args.image.id} className="block mx-auto aspect-4/3 object-cover outline-2 border-3 outline-[var(--button_bg)] border-[var(--bg-1)] rounded-2xl"></img>
      <p className="block w-auto text-center mt-2">{args.image.content}</p>  
    </div>
  );
}
