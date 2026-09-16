import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { UserTable } from '../typeorm/User';
import { DataSource, Repository } from 'typeorm';
import { CreateUserDto } from '../dtos/CreateUser.dto';
import { Multer } from 'multer';
import { AppDataSource } from 'src/typeorm/DataSource';
import { createReadStream } from 'fs';
import { join } from 'path';
import * as bcrypt from 'bcrypt';

@Injectable()
export class UserService {
  constructor(
    @InjectRepository(UserTable) private readonly userRepository: Repository<UserTable>){}

  async getUser(id:string){
    return this.userRepository.findOneBy({id})
  }

  async findUserByName(username:string){
    return this.userRepository.findOneBy({username})
  }
  
  async findUserByEmail(email:string){
    return this.userRepository.findOneBy({email})
  }

  async createUser(createUserDto:CreateUserDto){
      createUserDto.password = await bcrypt.hash(createUserDto.password, 10);
      const newUser = await this.userRepository.create(createUserDto)
      return this.userRepository.save(newUser)
  }
}
