import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TestTable, UserTable } from 'src/typeorm';
import { TestService } from './test.service';
import { TestController } from './test.controller';
import { UserService } from 'src/user/user.service';
@Module({
    imports: [TypeOrmModule.forFeature([TestTable,UserTable])],
    controllers: [TestController],
    providers: [TestService,UserService],
})
export class TestModule {}
