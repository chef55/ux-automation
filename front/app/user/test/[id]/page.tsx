//import "../globals.css";
export default function Home() {
  return (
    <div className="w-1/4 mx-auto mt-30">
        <form>
            <div className="">
                <label htmlFor="username" className="block text-sm/6 font-medium mt-2">Username</label>
                <div className="">
                    <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                        <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                        <input id="username" type="text" name="username"  className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6" />
                    </div>
                </div>
            </div>
           <div className="">
                <label htmlFor="password" className="block text-sm/6 font-medium mt-2">Password</label>
                <div className="">
                    <div className="flex items-center bg-[var(--bg-2)] pl-3 [border-image:var(--grad)_1] border-3 border-solid border-transparent transition-colors focus-within:bg-[var(--bg-3)]">
                        <div className="shrink-0 text-base text-gray-400 select-none sm:text-sm/6"></div>
                        <input id="password" type="password" name="password" className="block min-w-0 grow bg-transparent py-1.5 pr-3 pl-1 text-base focus:outline-none sm:text-sm/6 " />
                    </div>
                </div>
            </div>

            <input value="Log In" type="submit" className="mt-3 rounded-md bg-[var(--button_bg)] hover:bg-[var(--button_bgh)] transition-colors px-3 py-2 text-sm font-semibold text-background"></input>

            <div className="flex w-8/10 text-xs mt-2">
                <p>Don't have an account?</p>
                <a className="text-[var(--grg)] hover:text-[var(--grp)] transition-colors ml-1"href="/register">Create One!</a>
            </div>
            
        </form>
    </div>
  );
}
