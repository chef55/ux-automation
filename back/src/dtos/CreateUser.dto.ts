import { IsEmail, IsNotEmpty, MinLength } from "class-validator";
import { UserAlreadyExist } from "../validation/UserAlreadyExist";
import { EmailAlreadyExist } from "../validation/EmailAlreadyExist";


export class CreateUserDto{
    
    @EmailAlreadyExist({message:"Email already taken"})
    @IsEmail({},{message:"Invalid email"})
    email:string;

    @UserAlreadyExist({message:"Username already taken"})
    @IsNotEmpty({message:"Username cannot be empty"})
    username:string;

    @MinLength(5,{message:"Password too short"})
    @IsNotEmpty({message:"Password cannot be empty"})
    password:string;
}