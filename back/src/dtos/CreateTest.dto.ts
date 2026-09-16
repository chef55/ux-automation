import { isNotEmpty, IsNotEmpty } from "class-validator";
import { UserTable } from "src/typeorm";
import { IntegerType } from "typeorm";


export class CreateTestDto{
    @IsNotEmpty()
    name:string

    @IsNotEmpty()
    url:string

    @IsNotEmpty()
    user_age=0;

    @IsNotEmpty()
    user_literacy=0;

    @IsNotEmpty()
    tc=0;

    @IsNotEmpty()
    twe=0;

    @IsNotEmpty()
    user
}