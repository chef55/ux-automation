"use client"
import { useContext, useEffect, useRef, useState } from "react";
import Select, { ClassNamesConfig, StylesConfig } from "react-select";
import https from 'https'
import axios from "axios";
import { AuthIdContext } from "@/app/AuthContext";

//import "../globals.css";
export default function Home() {

    const [name, setName] = useState('');
    const [url, setUrl] = useState('');
    const [age, setAge] = useState('');
    const [literacy, setLiteracy] = useState('');
    const [scenarios, setScenarios] = useState<string[]>([])

    const [name_err, setNameErr] = useState('');
    const [url_err, setUrlErr] = useState('');
    const [age_err, setAgeErr] = useState('');
    const [literacy_err, setLiteracyErr] = useState('');

    const [name_valid, setNameValid] = useState(0);
    const [url_valid, setUrlValid] = useState(0);
    const [age_valid, setAgeValid] = useState(0);
    const [literacy_valid, setLiteracyValid] = useState(0);

    const [awaiting, setAwaiting] = useState(0)
    const [err, setErr] = useState('')



    const id = useContext(AuthIdContext)

    const options = [
        {value: "1", label: "Scenario 1"},
        {value: "2", label: "Scenario 2"},
        {value: "3", label: "Scenario 3"},
        {value: "4", label: "Scenario 4"},
    ]

    const [keyword, setKeyword] = useState('')
    const [scenario_arr, setScenarioArr] = useState<string[][]>([[]])
    const [scenario_arr_valid, setScenarioArrValid] = useState(0)
    const [scenario_arr_err, setScenarioArrErr] = useState("")

    function handleNameOnblur(e:any){
        e.preventDefault()
        if(name.length==0){
            setNameErr("Имя не может быть пустым")
            setNameValid(0)
        }
        else if(name.length>15){
            setNameErr("Имя не может превышать 100 символов")
            setNameValid(0)
        }
        else{
            setNameErr("")
            setNameValid(1)
        }

    }   

    async function handleUrlOnblur(e:any){
        e.preventDefault()
        if(URL.canParse(url)){
             await fetch(url, { mode:'no-cors' })
            .then(() => {setUrlErr(""); setUrlValid(1)})
            .catch(() => {setUrlErr("Ресурс недоступен");setUrlValid(0)})
        }
        else{
            setUrlErr("Ссылка введена некорректно")
            setUrlValid(0)
        }
    }    

    function handleAgeOnblur(e:any){
        e.preventDefault()
        if(age < '23'){
            setAgeErr("Возраст должен быть не меньше 23")
            setAgeValid(0)
        }
        else if(age > '85'){
            setAgeErr("Возраст должен быть не больше 85")
            setAgeValid(0)
        }
        else{
            setAgeErr("")
            setAgeValid(1)
        }
    }   

    function handleLiteracyOnblur(e:any){
        e.preventDefault()
        if(parseInt(literacy) < 0){
            setLiteracyErr("Техническая грамотность должна быть не меньше 0")
            setLiteracyValid(0)
        }
        else if(parseInt(literacy) > 100){
            setLiteracyErr("Техническая грамотность должна быть не больше 100")
            setLiteracyValid(0)
        }
        else{
            setLiteracyErr("")
            setLiteracyValid(1)
        }
    }   

    async function handleSubmit(e:any){
        e.preventDefault()
        if(name_valid && url_valid && age_valid && literacy_valid && scenario_arr_valid){
            setAwaiting(1)
            await axios.post('http://localhost:3001/test/create', {name: name, user_age:  age, url: url, user_literacy:  String(0.6+parseFloat(literacy)*0.008), scenarios: scenario_arr}, {withCredentials:true}).then((res)=>window.location.replace('/test/'+res.data.id)).catch(e=>{
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


    function handleAddKeyword(sid:number, event:any){
        const scenarios = scenario_arr
        scenarios[sid].push(keyword)
        setScenarioArr([...scenarios])
        let array_valid=1
        for (const scenario of scenarios){
            if(scenario.length==0){
                array_valid=0
            }
        }
        event.target.previousSibling.value=''
        //setKeyword('')
        setScenarioArrValid(array_valid)
        setScenarioArrErr(array_valid?"":"Каждый сценарий должен содержать хотя бы одно ключевое слово")
    }

    function handleDeleteKeyword(sid:number, kid:number){
        const scenarios = scenario_arr
        scenarios[sid].splice(kid, 1)
        setScenarioArr([...scenarios])
        let array_valid=1
        for (const scenario of scenarios){
            if(scenario.length==0){
                array_valid=0
            }
        }
        setScenarioArrValid(array_valid)
        setScenarioArrErr(array_valid?"":"Каждый сценарий должен содержать хотя бы одно ключевое слово")
    }

    
    function handleAddScenario(){
        setScenarioArr([...scenario_arr,[]])
        let array_valid=1
        for (const scenario of [...scenario_arr,[]]){
            if(scenario.length==0){
                array_valid=0
            }
        }
        setScenarioArrValid(array_valid)
        setScenarioArrErr(array_valid?"":"Каждый сценарий должен содержать хотя бы одно ключевое слово")
    }

    function handleDeleteScenario(sid:number){
        const scenarios = scenario_arr
        scenarios.splice(sid, 1)
        //setScenarioArr([...scenarios,['']])
        setScenarioArr([...scenarios])
                let array_valid=1
        for (const scenario of scenarios){
            if(scenario.length==0){
                array_valid=0
            }
        }
        setScenarioArrValid(array_valid)
        setScenarioArrErr(array_valid?"":"Каждый сценарий должен содержать хотя бы одно ключевое слово")
    }


  return (
    id!=-1?
        !awaiting?<div className="w-1/4 mx-auto mt-30 flex-1">
            <form onSubmit={handleSubmit}>
                <div className="">
                    <label htmlFor="name" className="block text-sm/6 font-medium mt-2">Название тестирования</label>
                    <div className="">
                        <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                            <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                            <input onBlur={handleNameOnblur} onChange={(e)=>{setName(e.target.value)}} id="name" type="text" name="name"  className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6" />
                        </div>
                        <p className="text-sm/6 text-[var(--error)]">{name_err}</p>
                    </div>
                </div>
            <div className="">
                    <label htmlFor="url" className="block text-sm/6 font-medium mt-2">Ссылка на страницу</label>
                    <div className="">
                        <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                            <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                            <input onBlur={handleUrlOnblur} onChange={(e)=>{setUrl(e.target.value)}} id="url" type="text" name="url" className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6 " />
                        </div>
                        <p className="text-sm/6 text-[var(--error)]">{url_err}</p>
                    </div>
                </div>

            <div className="">
                    <label htmlFor="age" className="block text-sm/6 font-medium mt-2">Возраст пользователей</label>
                    <div className="">
                        <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                            <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                            <input onBlur={handleAgeOnblur} onChange={(e)=>{setAge(e.target.value)}} placeholder="23-80" id="age" type="number" name="age" className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6 " />
                        </div>
                        <p className="text-sm/6 text-[var(--error)]">{age_err}</p>
                    </div>
                </div>

                <div className="">
                    <label htmlFor="literacy" className="block text-sm/6 font-medium mt-2">Техническая грамотность пользователей</label>
                    <div className="">
                        <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                            <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                            <input onBlur={handleLiteracyOnblur} onChange={(e)=>{setLiteracy(e.target.value)}} placeholder="0-100" id="literacy" type="number" name="literacy" className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6 " />
                        </div>
                        <p className="text-sm/6 text-[var(--error)]">{literacy_err}</p>
                    </div>
                </div>

                <div className="">
                    <p className="mt-2 border-b border-[var(--button_bgh)">Сценарии</p>
                    {scenario_arr.map((scenario,sid)=>
                    <div className=" border-b border-[var(--button_bgh) mt-2">
                        <p onClick={()=>{handleDeleteScenario(sid)}}>Сценарий {sid+1}</p>
                        <div className="flex flex-wrap gap-1 align-center mb-3">
                            <p className="w-fit p-1 mt-1 border-3 border-[var(--bg-1)]">Ключевые слова: </p>{scenario.map((keyword,kid)=><p className="max-w-full h-max overflow-clip cursor-pointer w-fit bg-[var(--bg-3)] border-[var(--bg-3)] border-3 border-solid px-2 py-1 mt-1 " onClick={(e:any)=>handleDeleteKeyword(sid,kid)}>{keyword} &#10006;</p>)}
                            <div className=" w-1/3 flex items-center bg-[var(--bg-2)] px-2 py-1 mt-1 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                                <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                                <input onChange={e=>setKeyword(e.target.value)} id="keyword" type="text" name="keyword" className="block  min-w-0 grow bg-transparent text-base focus:outline-none sm:text-sm/6 " />
                                <p className="cursor-pointer" onClick={(e)=>handleAddKeyword(sid,e)}>&#128932;</p>
                            </div>
                        </div>
                    </div>)}
                    <p className="text-sm/6 text-[var(--error)]">{scenario_arr_err}</p>
                    <div className='mt-2 cursor-pointer'onClick={handleAddScenario}>Добавить сценарий</div>
                    
                </div>

                {/*<div className="">
                    <label htmlFor="" className="block text-sm/6 font-medium mt-2">Scenarios</label>
                    <Select onBlur={handleScenarioOnblur} onChange={handleScenarioOnChange} styles={styles} closeMenuOnSelect={false} isMulti options={options}></Select>
                    <p className="text-sm/6 text-[var(--error)]">{scenario_err}</p>
                </div>*/}

                <input value="Создать" type="submit" className="mt-3 rounded-md bg-[var(--button_bg)] hover:bg-[var(--button_bgh)] transition-colors px-3 py-2 text-sm font-semibold text-background"></input>
                
            </form>
        </div>
        :<div className="mt-30 text-center text-3xl">Тестирование в процессе выполнения, ожидайте <br/>
            <p className="text-red-800">{err}</p>
        </div>
    :<div className="flex justify-center flex-1">
        <p className="mt-40 text-3xl"><a className="text-[var(--grg)] hover:text-[var(--grp)] transition-colors ml-1" href="/auth">Авторизуйтесь</a> для создания тестирования</p>
    </div>
  );
}
