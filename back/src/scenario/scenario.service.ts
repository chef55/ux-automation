import { Injectable, StreamableFile } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { In, IntegerType, Repository } from 'typeorm';
import { ImageTable, ScenarioTable, TestTable, UserTable } from 'src/typeorm';
import { UserService } from 'src/user/user.service';
import { AppDataSource } from 'src/typeorm/DataSource';
import fs from 'fs'
import { join } from 'path';
//import 

@Injectable()
export class ScenarioService {
  constructor(
    @InjectRepository(ScenarioTable) private readonly scenarioRepository: Repository<ScenarioTable>){}

  async getScenarioData(id:string){
    const scen= await this.scenarioRepository.findOneBy({id})
    //const reply = { name: test.name, url: test.url, success_rate: test.success_rate, time_spent: test.time_spent }
    return scen
  }

  async getScenarioImages(id:string){
    const arr = await AppDataSource.getRepository(ImageTable).createQueryBuilder('image').leftJoinAndSelect('image.scenario','scenario').where('image."scenarioId"=:id',{id:id}).getMany()
    const images=[]
    arr.map((e)=>{
        images.push({id: e.id, content: e.content})
    })
    return {images: images}
  }

}
