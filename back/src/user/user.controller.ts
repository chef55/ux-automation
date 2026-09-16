import { Body, Controller, Get, HttpStatus, Param, ParseFilePipeBuilder, Post, Res, UploadedFile, UseGuards, UseInterceptors } from '@nestjs/common';
import { UserService } from './user.service';
import { CreateUserDto } from '../dtos/CreateUser.dto';
import { Session } from '@nestjs/common'
import { FileInterceptor } from '@nestjs/platform-express';
import { AuthenticatedGuard } from 'src/auth/local-auth.guard';
import { join } from 'path';
import { of } from 'rxjs';

@Controller('user')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @UseGuards(AuthenticatedGuard)
  @Get()
  getUser(@Session() session:Record<string,any>) {
    return this.userService.getUser(session.passport.user.id);
  }
  
  @Post('create')
  createUser(@Body() createUserDto:CreateUserDto){
    return this.userService.createUser(createUserDto)
  }
}
