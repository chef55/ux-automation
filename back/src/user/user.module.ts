import { Module } from '@nestjs/common';
import { UserService } from './user.service';
import { UserController } from './user.controller';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UserTable } from 'src/typeorm/User';
import { MulterModule } from '@nestjs/platform-express';
import { diskStorage } from 'multer';
@Module({
    imports: [TypeOrmModule.forFeature([UserTable]), /*MulterModule.registerAsync({
        useFactory: async ()=>(await {
            storage:await diskStorage({
                destination: '../uploads',
                filename: (req,file,cb)=>{
                  return cb(null, Date.now().toString()+"."+file.mimetype.split('/')[1].toString())
                }
            })
        })
    })*/],
    controllers: [UserController],
    providers: [UserService],
    exports:[UserService]
})
export class UserModule {}
