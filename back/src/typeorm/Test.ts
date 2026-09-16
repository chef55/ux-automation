import { Column, CreateDateColumn, Entity, Index, IsNull, ManyToOne, OneToMany, OneToOne, PrimaryGeneratedColumn } from "typeorm";
import { UserTable } from "./User";
import { ScenarioTable } from "./Scenario";

@Entity()
export class TestTable{
    @PrimaryGeneratedColumn({
        type: 'bigint',
        name:'test_id',
    })
    id:string;

    @Column('varchar')
    name='';

    @Column('varchar')
    url='';

    @Column('integer')
    user_age=0;

    @Column('integer')
    std_age=0;

    @Column('real')
    user_literacy=0;

    @Column('real')
    std_literacy=0;

    @Column('real')
    tc=0;

    @Column('real')
    twe=0;

    @CreateDateColumn()
    creation_date

    @Column('bigint')
    expiredAt=Date.now()+31557600000

    @ManyToOne(()=>UserTable, (user)=>user.tests, { onDelete: 'CASCADE' })
    user: UserTable

    @OneToMany(()=>ScenarioTable, (scenario)=>scenario.test)
    scenarios: ScenarioTable[]
}