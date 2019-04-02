# Created by hborcher at 2/2/2018
Feature: Build package objects
  # You should easily be able to build a new package object using the package factory

  Scenario Outline: Loading session containing 2 objects
    Given We have a object created by contains files that belong to two groups
    Then resulting packages should be 2
    And the first object should contain everything from the first group
    And the second object should contain everything from the second group
    Examples:
      | package_type             |
      | CaptureOnePackage        |
      | HathiTiff                |
      | DigitalLibraryCompound   |


  Scenario: Hathi TIFF package containing 2 objects with sidecar text files
    Given a hathi tiff package containing 2 objects with text sidecar files
    Then resulting packages hathi tiff package should be 2
    And each instance of tiff package in should contain a text sidecar file

  Scenario: Hathi jp2 package containing 2 objects with sidecar text files
    Given a hathi jp2 package containing 2 objects with text sidecar files
    Then resulting packages hathi jp2 package should be 2
    And each instance in jp2 package should contain a text sidecar file
