import { IsNotEmpty } from "class-validator";


export class LogInDto{
    @IsNotEmpty({message:"Incorrect username or password"})
    username:string;

    @IsNotEmpty({message:"Incorrect username or password"})
    password:string;
}