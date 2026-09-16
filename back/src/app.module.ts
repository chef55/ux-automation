import { Module } from '@nestjs/common';
import { UserModule } from './user/user.module';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AuthModule } from './auth/auth.module';
import { PassportModule } from '@nestjs/passport';
import entities from './typeorm';
import { TestModule } from './test/test.module';
import { ScenarioModule } from './scenario/scenario.module';
import { ImageModule } from './image/image.module';

@Module({
  imports: [UserModule, AuthModule, TestModule, ScenarioModule, ImageModule, ScenarioModule,
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: 'localhost',
      port: 5432,
      username: 'username',
      password: 'password',
      database: 'database',
    entities,
    synchronize:true
    }),
    PassportModule.register({session:true})],
  controllers: [],
  providers: [],
})
export class AppModule {}
