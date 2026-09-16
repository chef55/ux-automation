import { InjectRepository } from '@nestjs/typeorm';
import {
    registerDecorator,
    ValidationOptions,
    ValidatorConstraint,
    ValidatorConstraintInterface,
    ValidationArguments,
  } from 'class-validator';
import { UserTable } from 'src/typeorm';
import { AppDataSource } from 'src/typeorm/DataSource';
import { Repository } from 'typeorm';



@ValidatorConstraint({ async: true })
export class UserAlreadyExistConstraint implements ValidatorConstraintInterface {
  validate(username: any, args: ValidationArguments) {
    const userRepository = AppDataSource.getRepository(UserTable)
    return userRepository.findOneBy({username}).then(user => {
      if (user) return false;
      return true;
    });
  }
}

export function UserAlreadyExist(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      constraints: [],
      validator: UserAlreadyExistConstraint,
    });
  };
}