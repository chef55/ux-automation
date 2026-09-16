import { Injectable, StreamableFile } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { ImageTable } from 'src/typeorm';
import { Repository } from 'typeorm';
//import 

@Injectable()
export class ImageService {
  constructor(
    @InjectRepository(ImageTable) private readonly imageRepository: Repository<ImageTable>){}
    
    
    async getImageData(id:string){
      const scen= await this.imageRepository.findOneBy({id})
      //const reply = { name: test.name, url: test.url, success_rate: test.success_rate, time_spent: test.time_spent }
      return scen
    }
}
