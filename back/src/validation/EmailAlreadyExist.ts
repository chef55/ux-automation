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



@ValidatorConstraint({ async: true })
export class EmailAlreadyExistConstraint implements ValidatorConstraintInterface {
  validate(email: any, args: ValidationArguments) {
    const userRepository = AppDataSource.getRepository(UserTable)
    return userRepository.findOneBy({email}).then(user => {
      if (user) return false;
      return true;
    });
  }
}

export function EmailAlreadyExist(validationOptions?: ValidationOptions) {
  return function (object: Object, propertyName: string) {
    registerDecorator({
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      constraints: [],
      validator: EmailAlreadyExistConstraint,
    });
  };
}