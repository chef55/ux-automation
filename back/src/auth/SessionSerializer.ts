import { CanActivate, ExecutionContext, Inject } from "@nestjs/common";
import { PassportSerializer } from "@nestjs/passport";
import { Observable } from "rxjs";
import { UserTable } from "src/typeorm/User";
import { UserService } from "src/user/user.service";


export class SessionSerializer extends PassportSerializer{
    constructor(@Inject('USER_SERVICE')
        private readonly userService:UserService){super()}

    serializeUser(user: UserTable, done: (err,user:UserTable)=>void) {
        done(null,user)
    }
    
    async deserializeUser(user: UserTable, done: (err,user:UserTable)=>void) {
        const userDB = await this.userService.getUser(user.id)
        return userDB?done(null,userDB):done(null,null)
    }
}

