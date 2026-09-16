'use client'
import axios from "axios";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Image from "./Image";

//import "../globals.css";
export default function Scenario(args:any) {
    const id = args.scenario
    const [keywords, setKeywords] = useState([])
    const [eit, setEIT] = useState(0)
    const [tei, setTEI] = useState(0)
    const [ct, setCT] = useState('')
    const [images, setImages] = useState([])
    const [loading, setLoading] = useState(1)
    useEffect(() => {
        async function fetchData(){
            await axios.get('http://localhost:3001/scenario/'+id, {withCredentials:true})
            .then(res => {
                setKeywords(res.data.keywords)
                setEIT(res.data.eit)
                setTEI(res.data.tei)
                setCT(res.data.ct)
            });
        }
        fetchData();
    }, [id]);

    useEffect(() => {
        async function fetchData(){
            await axios.get('http://localhost:3001/scenario/'+id+'/images', {withCredentials:true})
            .then(res => {
                setImages(res.data.images)
                setLoading(0)
            });
        }
        fetchData();
    }, [id]);



  return (
    loading?<p>Тестирование в работе</p>
    :<div className="mt-15">
        <p className="text-2xl">Сценарий {args.index}</p>
        <div className="w-auto mx-auto mt-1 border-t-2">
            <p className="mt-3">Ключевые слова: {keywords.join(", ")}</p>
            <p className="mt-3">Ошибки в задаче: {eit}</p>
            <p className="mt-1">Интенсивность ошибок задачи: {tei}</p>
            <p className="mt-1">Время выполнения задачи: {ct}</p>
            <div className="grid grid-cols-2 justify-items-center">
                {images.map(image=> <Image setOverlayId={args.setOverlayId} setOverlayText={args.setOverlayText} image={image}></Image> )}
            </div>
        </div>
    </div>
  );
}
