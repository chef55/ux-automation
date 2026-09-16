'use client'
import { useState } from "react";
import "../globals.css";
import axios from "axios";
export default function Home() {

    const [username, setUsername] = useState('');
    const [pass, setPass] = useState('');
    const [err, setErr] = useState('');
    const [username_err, setUsernameErr] = useState('');
    const [pass_err, setPassErr] = useState('');
    const [username_valid, setUsernameValid] = useState(0);
    const [pass_valid, setPassValid] = useState(0);

    
    function handlePasswordOnblur(e:any){
        e.preventDefault()
        if(pass.length==0){
            setPassErr("Паролъ не может быть пустым")
        }
        else if(pass.length>15){
            setPassErr("Пароль слишком длинный")
        }
        else{
            setPassErr("")
            setPassValid(1)
        }

    }

    function handleUsernameOnblur(e:any){
        e.preventDefault()
        if(username.length==0){
            setUsernameErr("Имя пользователя не может быть пустым")
        }
        else if(username.length>12){
            setUsernameErr("Имя пользователя слишком длинное")
        }
        else{
            setUsernameErr("")
            setUsernameValid(1)
        }
    }

    async function handleSubmit(e:any) {
        e.preventDefault()
        if(pass_valid && username_valid){
            await axios.post('http://localhost:3001/auth', {username: username, password: pass}, {withCredentials:true}).then(()=>window.location.replace('/user')).catch(e=>{
                if(e.response){
                    if(e.response.status>=500){
                    setErr('Ошибка сервера, повторите попытку позже');
                    }
                    else{
                    setErr(e.response.data.message);
                    }
                }
                else if(e.request){
                    setErr('Ошибка сервера, повторите попытку позже');
                }
            })
        }
    }

    return (
    <div className="w-1/4 mx-auto mt-30 flex-1">
        <form onSubmit={handleSubmit}>
            <div className="">
                <label htmlFor="username" className="block text-sm/6 font-medium mt-2">Имя пользователя</label>
                <div className="">
                    <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                        <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                        <input autoFocus onBlur={handleUsernameOnblur} onChange={(e)=>{setUsername(e.target.value)}} id="username" type="text" name="username"  className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6" />
                    </div>
                    <p className="text-sm/6 text-[var(--error)]">{username_err}</p>
                </div>
            </div>
           <div className="">
                <label htmlFor="password" className="block text-sm/6 font-medium mt-2">Пароль</label>
                <div className="">
                    <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                        <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                        <input onBlur={handlePasswordOnblur} onChange={(e)=>{setPass(e.target.value)}} id="password" type="password" name="password" className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6 " />
                    </div>
                    <p className="text-sm/6 text-[var(--error)]">{pass_err}</p>
                </div>
            </div>
            <p className="text-sm/6 text-[var(--error)]">{err}</p>
            <input value="Войти" type="submit" className="mt-3 rounded-md bg-[var(--button_bg)] hover:bg-[var(--button_bgh)] transition-colors px-3 py-2 text-sm font-semibold text-background"></input>
            <div className="flex w-8/10 text-xs mt-2">
                <p>Нет учетной записи?</p>
                <a className="text-[var(--grg)] hover:text-[var(--grp)] transition-colors ml-1"href="/register">Создайте её!</a>
            </div>
            
        </form>
    </div>
  );
}
