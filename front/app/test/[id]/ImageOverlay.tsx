import axios from "axios";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

//import "../globals.css";
export default function ImageOverlay(args:any) {

  const theme = window.matchMedia('(prefers-color-scheme: dark)').matches?"scheme-dark":"";

  return (
    <div  className="fixed w-screen h-screen top-0 right-0">
      <div onClick={()=>args.setOverlayId('')} className="w-full h-full [backdrop-filter:blur(2px)] cursor-pointer" ></div>
      <div className="absolute top-[50%] left-[50%] transform-[translate(-50%,-50%)] w-2/3 h-5/6 bg-[var(--bg-3)] border-2 border-[var(--bg-3)] [box-shadow:0_0_25px_#090909]">
        <div className="h-[5%] px-3 flex justify-between items-center">
          <p>{args.text}</p>
          <div onClick={()=>args.setOverlayId('')} className="cursor-pointer">Закрыть</div>
        </div>
        <div className={"bg-background overflow-y-auto pt-3 pb-3 h-[95%] flex items-center "+theme}>
          <img src={'http://localhost:3001/image/'+args.id} className="block m-auto w-10/12"></img>
        </div>
      </div>
    </div>
  );
}
