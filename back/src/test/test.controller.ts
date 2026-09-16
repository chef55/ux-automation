import { Body, Controller, Get, HttpStatus, Param, ParseFilePipeBuilder, Post, Res, StreamableFile, UploadedFile, UseGuards, UseInterceptors } from '@nestjs/common';
import { TestService } from './test.service';
import { CreateTestDto } from '../dtos/CreateTest.dto';
import { AuthenticatedGuard } from 'src/auth/local-auth.guard';
import { FileInterceptor } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import { Session } from '@nestjs/common'
import { UserService } from 'src/user/user.service';
import { of } from 'rxjs';
import { join } from 'path';
import { createReadStream } from 'fs';

@Controller('test')
export class TestController {
  constructor(private readonly testService: TestService) {}

  @UseGuards(AuthenticatedGuard)
  @Get()
  getUserTests(@Session() session:Record<string,any>) {
    return this.testService.getUserTests( session.passport.user.id )
  }
  
  @UseGuards(AuthenticatedGuard)
  @Get(':id')
  getTestData(@Param() params:any) {
    return this.testService.getTestData(params.id);
  }
  
  @UseGuards(AuthenticatedGuard)
  @Get(':id/owner')
  getTestOwner(@Param() params:any, @Session() session:Record<string,any>) {
    return this.testService.getTestOwner(params.id, session);
  }

  @UseGuards(AuthenticatedGuard)
  @Get(':id/scenarios')
  getTestScenarios(@Param() params:any) {
    return this.testService.getTestScenarios(params.id);
  }

  @UseGuards(AuthenticatedGuard)
  @Get(':id/delete')
  getTestDelete(@Param() params:any, @Session() session:Record<string,any>) {
    return this.testService.deleteTest(params.id, session);
  }

  @UseGuards(AuthenticatedGuard)
  @Post('create')
  createTest(@Body() params:any, @Session() session:Record<string,any>) {
    return this.testService.createTest( params,session )
  }
}
