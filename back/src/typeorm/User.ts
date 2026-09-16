import { Column, Entity, OneToMany, PrimaryGeneratedColumn } from "typeorm";
import { TestTable } from "./Test";

@Entity()
export class UserTable{
    @PrimaryGeneratedColumn({
        type: 'bigint',
        name:'user_id',
    })
    id:string;

    @Column('varchar')
    email='';

    @Column('varchar')
    username='';

    @Column('varchar')
    password='';

    @OneToMany(()=>TestTable, (test)=>test.user)
    tests: TestTable[]
}