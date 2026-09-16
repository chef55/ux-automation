import Image from "next/image";
import Header from "./Header";
import Footer from "./Footer";

export default function Home() {
  return (
    <><div className="items-center mt-30 flex-1">
      <div className="flex justify-between gap-10 w-2/3 m-auto text-justify">
        <div className="w-3/10">UXLab - ваше универсальное решение для тестирования интерфейсов</div>
        <div className="w-px grow-[0 0 1] bg-[var(--border)]"></div>
        <div className="w-6/10">Мы предоставляем возможность проведения автоматизированного тестирования качетва интерфейсов.
        Просто укажите ссылку на вашу страницу, портрет целевого пользователя
        и сценарии тестирования и получите наглядный отчет о тестировании за
        считаные минуты.
        </div>
      </div>
    </div>
    <Footer></Footer></>
  );
}
