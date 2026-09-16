'use client'
import { useContext, useEffect, useState } from "react";
import "../globals.css";
import TableLine from "./TableLine";
import axios from "axios";
import { AuthContext, AuthIdContext } from "../AuthContext";

export default function Home() {

    const username = useContext(AuthContext)
    const id = useContext(AuthIdContext)


    const [tests, setTests] = useState([{}])

    useEffect(() => {
        async function fetchData(){
            axios.get('http://localhost:3001/test', {withCredentials:true})
            .then(res => {setTests(res.data.tests)})
            .catch(err => {
            console.log(err);});
        }
        if(id!=-1){
            fetchData();
        }
    }, [id]);

    
  async function handleLogOut(e:any) {
    await axios.get('http://localhost:3001/auth/delete', {withCredentials:true})
    .then(()=>window.location.replace('/'))
    .catch(()=>window.location.replace('/'));
  }

  return (
    id!=-1?<div className="w-3/5 mx-auto mt-20 flex-1">
        <div className="w-1/4 flex justify-between">
            <p>{username}</p>
            <a onClick={handleLogOut} className="cursor-pointer">Выйти</a>
        </div>
        <div className="border-t [border-image:var(--grad)_1] mt-5"></div>
        <div className="mt-10 w-5/6 mx-auto">
            {tests.length==0
            ?<p className="block text-3xl py-2 text-center">У вас пока нет тестирований</p>
            :<>
                <a className="py-2 flex text-center">
                    <p className="w-1/4">Название</p>
                    <p className="w-1/4">Дата</p>
                    <p className="w-3/8">Страница</p>
                    <p className="w-1/8"></p>
                </a>
                {tests.slice(0).reverse().map(test => <TableLine test={test}></TableLine>)}
            </>
            }
            
        </div>
    </div>
    :<div className="flex justify-center flex-1">
        <p className="mt-40 text-3xl"><a className="text-[var(--grg)] hover:text-[var(--grp)] transition-colors ml-1" href="/auth">Войдите</a> для просмотра истории</p>
    </div>
  );
}
