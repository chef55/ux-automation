import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ScenarioTable, TestTable, UserTable } from 'src/typeorm';
import { ScenarioService } from './scenario.service';
import { ScenarioController } from './scenario.controller';
import { TestService } from 'src/test/test.service';
@Module({
    imports: [TypeOrmModule.forFeature([TestTable,ScenarioTable])],
    controllers: [ScenarioController],
    providers: [ScenarioService,TestService],
})
export class ScenarioModule {}
