'use client'
import axios from "axios";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useContext, useEffect, useState } from "react";
import Scenario from "./Scenario";
import ImageOverlay from "./ImageOverlay";
import { AuthContext, AuthIdContext } from "@/app/AuthContext";

//import "../globals.css";
export default function Home() {
    const router = useRouter()
    const params = useParams()
    const id = params.id
    const [name, setName] = useState('')
    const [url, setUrl] = useState('')
    const [age, setAge] = useState(0)
    const [literacy, setLiteracy] = useState(0)
    const [tc, setTC] = useState(0)
    const [twe, setTWE] = useState(0)
    const [date, setDate] = useState('')
    const [scenarios, setScenarios] = useState([])
    const [overlay_id, setOverlayId] = useState('')
    const [overlay_text, setOverlayText] = useState('')
    const [owner, setOwner] = useState(0)
    const [loading, setLoading] = useState(1)
    const session_id = useContext(AuthIdContext)

    useEffect(() => {
        async function fetchData(){
            await axios.get('http://localhost:3001/test/'+id+'/owner', {withCredentials:true})
            .then(res => {
                setOwner(res.data)
            });
        }
        if(session_id!=-1) fetchData();
        else setLoading(0)
    }, [id,session_id]);


    useEffect(() => {
        async function fetchData(){
            await axios.get('http://localhost:3001/test/'+id, {withCredentials:true})
            .then(res => {
                setName(res.data.name)
                setUrl(res.data.url)
                setAge(res.data.user_age)
                setLiteracy(res.data.user_literacy)
                setTC(res.data.tc)
                setTWE(res.data.twe)
                setDate(String(res.data.creation_date).split('T')[0]+ " " + String(res.data.creation_date).split('T')[1].split(".")[0])
                setLoading(0)
            });
        }
        if(owner) fetchData();
    }, [owner]);

    useEffect(() => {
        async function fetchData(){
            await axios.get('http://localhost:3001/test/'+id+'/scenarios', {withCredentials:true})
            .then(res => {
                setScenarios(res.data.ids)
            });
        }
        if(owner) fetchData();
    }, [owner]);


    async function handleDelete(e:any) {
        async function fetchData(){
            await axios.get('http://localhost:3001/test/'+id+'/delete', {withCredentials:true})
            .then(()=>window.location.replace('/user'))
            .catch(()=>window.location.replace('/user'));
        }
        if(owner) fetchData()
        else ()=>window.location.replace('/auth');
    }

  return (
    loading?<div className="w-1/2 h-full mx-auto mt-30 flex-1"><p>Загрузка</p></div>
    :session_id!=-1?owner?<div className="w-1/2 h-full mx-auto mt-30 flex-1">
        <div className="flex w-auto justify-between">
            <p>{name}</p> <p>{date}</p> <p onClick={handleDelete} className="text-red-800 cursor-pointer">Удалить</p>
        </div>
        <p>Ссылка на страницу: {url}</p>
        <p>Возраст пользователей: {age}</p>
        <p>Техническая грамотность пользователей: {Math.round((literacy-0.6)/0.008)}</p>
        <p>Выполненные задачи: {tc}</p>
        <p>Задачи с ошибками: {twe}</p>
        {scenarios.map((scenario,i) => <Scenario index={i+1} setOverlayId={setOverlayId} setOverlayText={setOverlayText} scenario={scenario}></Scenario>)}
        {
            overlay_id===''?<></>:<ImageOverlay id={overlay_id} text={overlay_text} setOverlayId={setOverlayId}></ImageOverlay>
        }
    </div>
    :<div className="h-full flex justify-center flex-1">
        <p className="mt-40 text-3xl">Вы можете просматривать только собственные тестирования</p>
    </div>
    :<div className="h-full flex justify-center flex-1">
        <p className="mt-40 text-3xl"><a className="text-[var(--grg)] hover:text-[var(--grp)] transition-colors ml-1" href="/auth">Авторизуйтесь</a> для просмотра тестирований</p>
    </div>
  );
}
