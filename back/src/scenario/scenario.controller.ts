import { Body, Controller, Get, HttpStatus, Param, ParseFilePipeBuilder, Post, Res, StreamableFile, UploadedFile, UseGuards, UseInterceptors } from '@nestjs/common';
import { ScenarioService } from './scenario.service';
import { CreateTestDto } from '../dtos/CreateTest.dto';
import { AuthenticatedGuard } from 'src/auth/local-auth.guard';
import { FileInterceptor } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
import { Session } from '@nestjs/common'
import { UserService } from 'src/user/user.service';
import { of } from 'rxjs';
import { join } from 'path';
import { createReadStream } from 'fs';

@Controller('scenario')
export class ScenarioController {
  constructor(private readonly scenarioService: ScenarioService) {}

  @UseGuards(AuthenticatedGuard)
  @Get(':id')
  getScenarioData(@Param() params:any) {
    return this.scenarioService.getScenarioData(params.id);
  }

  @UseGuards(AuthenticatedGuard)
  @Get(':id/images')
  getScenariosImages(@Param() params:any) {
    return this.scenarioService.getScenarioImages(params.id);
  }
  
  /*@UseGuards(AuthenticatedGuard)
  @Get(':id/delete')
  deleteTest(@Param() params:any, @Session() session:Record<string,any>) {
    return this.testService.deleteTest( params.id,session )
  }*/
}
