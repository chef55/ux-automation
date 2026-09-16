import axios from "axios";
import "../globals.css";

export default function TableLine(test:any) {
  test = test.test
  let date = String(test.date).split('T')[0]+ " " + String(test.date).split('T')[1];
  date = date.split(".")[0]

  async function handleDelete(e:any) {
    await axios.get('http://localhost:3001/test/'+test.id+'/delete', {withCredentials:true})
    .then(()=>window.location.replace('/user'))
    .catch(()=>window.location.replace('/user'));
  }

  return (
    <a className="py-2 flex text-center border-t [border-image:var(--grad)_1]">
        <a href={"/test/"+test.id} className="overflow-hidden whitespace-nowrap text-ellipsis w-1/4">{test.name}</a>
        <a href={"/test/"+test.id} className="w-1/4">{date}</a>
        <a href={"/test/"+test.id} className="overflow-hidden whitespace-nowrap text-ellipsis w-3/8">{test.url}</a>
        <a onClick={handleDelete}className="text-red-800 w-1/8 cursor-pointer hover:text-red-600 transition-colors">Удалить</a>
    </a>
  );
}
