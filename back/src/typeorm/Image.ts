import { Column, CreateDateColumn, Entity, Index, IsNull, ManyToOne, OneToMany, OneToOne, PrimaryGeneratedColumn } from "typeorm";
import { UserTable } from "./User";
import { Test } from "@nestjs/testing";
import { TestTable } from "./Test";
import { ScenarioTable } from "./Scenario";

@Entity()
export class ImageTable{
    @PrimaryGeneratedColumn({
        type: 'bigint',
        name:'image_id',
    })
    id:string;

    @Column('varchar')
    content=0;

    @ManyToOne(()=>ScenarioTable, (scenario)=>scenario.images, { onDelete: 'CASCADE' })
    scenario: ScenarioTable
}