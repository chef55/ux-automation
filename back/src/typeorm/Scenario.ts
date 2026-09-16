import { Column, CreateDateColumn, Entity, Index, IsNull, ManyToOne, OneToMany, OneToOne, PrimaryGeneratedColumn } from "typeorm";
import { UserTable } from "./User";
import { Test } from "@nestjs/testing";
import { TestTable } from "./Test";
import { ImageTable } from "./Image";

@Entity()
export class ScenarioTable{
    @PrimaryGeneratedColumn({
        type: 'bigint',
        name:'scenario_id',
    })
    id:string;

    @Column('varchar', {array:true})
    keywords=[];

    @Column('real')
    eit=0;

    @Column('real')
    tei=0;

    @Column('time')
    ct='00:00:00';

    @ManyToOne(()=>TestTable, (test)=>test.scenarios, { onDelete: 'CASCADE' })
    test: TestTable

    @OneToMany(()=>ImageTable, (image)=>image.scenario)
    images: ImageTable[]
}