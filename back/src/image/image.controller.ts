import { Body, Controller, Get, HttpStatus, Param, ParseFilePipeBuilder, Post, Res, StreamableFile, UploadedFile, UseGuards, UseInterceptors } from '@nestjs/common';
import { ImageService } from './image.service';
import { AuthenticatedGuard } from 'src/auth/local-auth.guard';
import { of } from 'rxjs';
import { join } from 'path';
import { createReadStream } from 'fs';

@Controller('image')
export class ImageController {
  constructor(private readonly imageService: ImageService) {}

  @UseGuards(AuthenticatedGuard)
  @Get(':id')
  getImage(@Param() params:any, @Res() res) {
    return of(res.sendFile(join(process.cwd(),'image_storage/',params.id + '.png')))
  }

  @UseGuards(AuthenticatedGuard)
  @Get(':id/data')
  getImageInfo(@Param() params:any) {
    return this.imageService.getImageData(params.id);
  }
}
