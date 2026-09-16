import { Injectable, StreamableFile } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { In, IntegerType, Repository } from 'typeorm';
import { CreateUserDto } from '../dtos/CreateUser.dto';
import { ScenarioTable, TestTable, UserTable } from 'src/typeorm';
import { CreateTestDto } from 'src/dtos/CreateTest.dto';
import { diskStorage } from 'multer';
import { UserService } from 'src/user/user.service';
import { createReadStream } from 'fs';
import { join } from 'path';
import { AppDataSource } from 'src/typeorm/DataSource';
import { spawnSync } from 'child_process';
//import 

@Injectable()
export class TestService {
  constructor(
    @InjectRepository(TestTable) private readonly testRepository: Repository<TestTable>){}

  async getTestData(id:string){
    const test= await this.testRepository.findOneBy({id})
    //const reply = { name: test.name, url: test.url, success_rate: test.success_rate, time_spent: test.time_spent }
    return test
  }
  
  async getTestOwner(id:string, session:Record<string,any>){
    const test= await AppDataSource.getRepository(TestTable).createQueryBuilder('test').select().where("id=:id",{id:id}).leftJoinAndSelect('test.user','user').where('user_id=:id',{id:session.passport.user.id}).getOne()
    if(test) return 1
    else return 0
  }

  async deleteTest(id:string, session:Record<string,any>){
    const test = await AppDataSource.getRepository(TestTable).createQueryBuilder('test').select().where("id=:id",{id:id}).leftJoinAndSelect('test.user','user').where('user_id=:id',{id:session.passport.user.id}).getOne()
    if(test||session.passport.user.id==1){
      await AppDataSource.createQueryBuilder().delete().from(TestTable).where('id=:id',{id:id}).execute()
      return true
    }
    return false
  }

  async getUserTests(id:string){
    const arr = await AppDataSource.getRepository(TestTable).createQueryBuilder('test').leftJoinAndSelect('test.user','user').where('user.id=:id',{id:id}).getMany()
    const tests=[]
    arr.map((e)=>{
      tests.push({name: e.name, id: e.id, date: e.creation_date, url: e.url})
    })
    return {tests: tests}
  }

    async getTestScenarios(id:string){
      const arr = await AppDataSource.getRepository(ScenarioTable).createQueryBuilder('scenario').leftJoinAndSelect('scenario.test','test').where('scenario."testId"=:id',{id:id}).getMany()
      const ids=[]
      arr.map((e)=>{
        ids.push(e.id)
      })
      return {ids: ids}
    }

  async createTest(params:any, session: Record<string,any>){
    //console.log(params.scenarios)
    let createTestDto = new CreateTestDto()
    const user = await AppDataSource.getRepository(UserTable).findOneBy({id:session.passport.user.id})
    createTestDto.name = params.name
    createTestDto.url = params.url
    createTestDto.user_age = params.user_age
    createTestDto.user_literacy = params.user_literacy
    createTestDto.user = user.id

    //console.log(createTestDto)
    const newTest = await this.testRepository.create(createTestDto)
    const res = await this.testRepository.save(newTest)
    //execute python here
    // доделать асинхронную обработку странички (возвращаем вустую запись, после обработки обновляем бд)

    const { spawn } = require('node:child_process');
    const childPython = spawnSync('python', ["src//test//test_modules//run_test.py", params.url, res.id, parseFloat(params.user_age), parseFloat(params.user_literacy), JSON.stringify(params.scenarios)]);
    console.log(`stderr: ${childPython.stderr}`);
    console.log(`stdout: ${childPython.stdout}`);

    return res
  }
}
