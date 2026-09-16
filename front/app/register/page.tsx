'use client'
import { useState } from "react";
import "../globals.css";
import axios from "axios";

export default function Home() {
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [pass, setPass] = useState('');
    const [passrep, setPassrep] = useState('');

    const [err, setErr] = useState('');
    
    const [email_err, setEmailErr] = useState('');
    const [username_err, setUsernameErr] = useState('');
    const [pass_err, setPassErr] = useState('');
    const [passrep_err, setPassrepErr] = useState('');

    const [email_valid, setEmailValid] = useState(0);
    const [username_valid, setUsernameValid] = useState(0);
    const [pass_valid, setPassValid] = useState(0);
    const [passrep_valid, setPassrepValid] = useState(0);

    function handlePasswordOnblur(e:any){
        e.preventDefault()
        if(!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@.#$!%*?&])[A-Za-z\d@.#$!%*?&]{5,15}$/.test(pass)){
            setPassValid(0);
            if(pass.length<5){
                setPassErr("Пароль не может быть короче 5 символов");
            }
            else if(pass.length > 15){
                setPassErr("Пароль не может быть длиннее 15 символов");
            }
            else if(!/^(?=.*[a-z])/.test(pass)){
                setPassErr("Пароль должен содержать хотя бы одну строчную букву");
            }
            else if(!/^(?=.*[A-Z])/.test(pass)){
                setPassErr("Пароль должен содержать хотя бы одну прописную букву");
            }
            else if(!/^(?=.*\d)/.test(pass)){
                setPassErr("Пароль должен содержать хотя бы одну цифру");
            }
            else if(!/^(?=.*[@$!%*?&])/.test(pass)){
                setPassErr("Пароль должен содержать хотя бы один специальный символ");
            }
        }
        else{
            setPassErr("");
            setPassValid(1);
        }
    }
    function handlePasswordRepeatOnblur(e:any){
        if(pass!=passrep){
            setPassrepValid(0);
            setPassrepErr("Пароли не совпадают");
        }
        else{
            setPassrepValid(1);
            setPassrepErr("");
        }
    }
    function handleUsernameOnblur(e:any){
        e.preventDefault()
        if(!/^[a-zA-Z0-9_]{4,12}$/.test(username)){
            setUsernameValid(0);
            if(username.length < 4){
                setUsernameErr("Имя пользователя не может быть короче 4 символов");
            }
            else if(username.length > 12){
                setUsernameErr("Имя пользователя не может быть длиннее 12 символов");
            }
            else if(!/^(?=.*[@$!%*?&])/.test(pass)){
                setUsernameErr("Имя пользователя содержит запрещенные символы");
            }
        }
        else{
            setUsernameValid(1);
            setUsernameErr("");
        }
    }
    function handleEmailOnblur(e:any){
        e.preventDefault()
        if(!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)){
            setEmailValid(0);
            setEmailErr("Почта введена некорректно");
        }
        else{
            setEmailValid(1);
            setEmailErr("");
        }
    }

    async function handleSubmit(e:any) {
        e.preventDefault()
        if(pass_valid && username_valid && email_valid && passrep_valid){
            await axios.post('http://localhost:3001/user/create', {email:email, username: username, password: pass}, {withCredentials:true}).then(()=>window.location.replace('/auth')).catch(e=>{
                if(e.response){
                    if(e.response.status>=500){
                        setErr('Ошибка сервера, повторите попытку позже');
                    }
                    else if(e.response.status==400){
                        e.response.data.message.map((err:any)=>{
                            if(err.property=="email"){
                                setEmailErr('Электронна почта уже использована');
                                setEmailValid(0);
                            }
                            if(err.property=="username"){
                                setUsernameErr('Пользователь уже существует');
                                setUsernameValid(0);
                            }
                        })
                    }
                    else{
                        setErr('Непредвиденная, повторите попытку позже');
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
                <label htmlFor="email" className="block text-sm/6 font-medium mt-2">Электронная почта</label>
                <div className="">
                    <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                        <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                        <input autoFocus onBlur={handleEmailOnblur} onChange={(e)=>{setEmail(e.target.value)}} id="email" type="text" name="email"  className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6" />
                    </div>
                    <p className="text-sm/6 text-[var(--error)]">{email_err}</p>
                </div>
            </div>
            <div className="">
                <label htmlFor="username" className="block text-sm/6 font-medium mt-2">Имя пользователя</label>
                <div className="">
                    <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                        <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                        <input onBlur={handleUsernameOnblur} onChange={(e)=>{setUsername(e.target.value)}} id="username" type="text" name="username"  className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6" />
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
                </div>
                <p className="text-sm/6 text-[var(--error)]">{pass_err}</p>
            </div>
            <div className="">
                <label htmlFor="password_repeat" className="block text-sm/6 font-medium mt-2">Повторите пароль</label>
                <div className="">
                    <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                        <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                        <input onBlur={handlePasswordRepeatOnblur} onChange={(e)=>{setPassrep(e.target.value)}} id="password_repeat" type="password" name="password_repeat" className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6 " />
                    </div>
                    <p className="text-sm/6 text-[var(--error)]">{passrep_err}</p>
                </div>
            </div>
            <p className="text-sm/6 text-[var(--error)]">{err}</p>
            <input value="Создать" type="submit" className="mt-3 rounded-md bg-[var(--button_bg)] hover:bg-[var(--button_bgh)] transition-colors px-3 py-2 text-sm font-semibold text-background"></input>
            
        </form>
    </div>
  );
}
